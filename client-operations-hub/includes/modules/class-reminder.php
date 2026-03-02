<?php
/**
 * Module C8: Reminder System
 *
 * Multi-channel reminders (Email + WordPress Admin).
 *
 * @package ClientOperationsHub
 */

namespace COH\Modules;

defined( 'ABSPATH' ) || exit;

class Reminder {

    /**
     * Initialize cron hooks.
     */
    public function init(): void {
        add_action( 'coh_process_reminders', array( $this, 'process_pending_reminders' ) );
        add_action( 'coh_daily_overdue_check', array( $this, 'check_overdue_tasks' ) );
        add_action( 'admin_notices', array( $this, 'show_admin_notices' ) );

        // Schedule cron events if not already scheduled.
        if ( ! wp_next_scheduled( 'coh_process_reminders' ) ) {
            wp_schedule_event( time(), 'hourly', 'coh_process_reminders' );
        }
        if ( ! wp_next_scheduled( 'coh_daily_overdue_check' ) ) {
            wp_schedule_event( strtotime( 'today 08:00' ), 'daily', 'coh_daily_overdue_check' );
        }
    }

    /**
     * Schedule a reminder for a task.
     */
    public static function schedule_for_task( int $task_id, int $client_id, string $due_date ): void {
        global $wpdb;

        $task = Task_Engine::get_task( $task_id );
        if ( ! $task ) {
            return;
        }

        $client = Client_Intake::get( $client_id );
        $company = $client ? $client['company_name'] : '';

        // Reminder on the due date at 08:00.
        $scheduled_at = $due_date . ' 08:00:00';

        $wpdb->insert( $wpdb->prefix . 'coh_reminders', array(
            'task_id'      => $task_id,
            'client_id'    => $client_id,
            'channel'      => 'email',
            'subject'      => sprintf( 'Aufgabe faellig: %s (%s)', $task['title'], $company ),
            'message'      => sprintf(
                "Folgende Aufgabe ist heute faellig:\n\n**%s**\nKunde: %s\nPrioritaet: %s\n\n%s",
                $task['title'],
                $company,
                ucfirst( $task['priority'] ),
                $task['description']
            ),
            'scheduled_at' => $scheduled_at,
            'status'       => 'pending',
        ) );

        // Also schedule an admin notification.
        $wpdb->insert( $wpdb->prefix . 'coh_reminders', array(
            'task_id'      => $task_id,
            'client_id'    => $client_id,
            'channel'      => 'admin',
            'subject'      => sprintf( 'Aufgabe faellig: %s (%s)', $task['title'], $company ),
            'message'      => $task['description'],
            'scheduled_at' => $scheduled_at,
            'status'       => 'pending',
        ) );
    }

    /**
     * Process all pending reminders that are due.
     */
    public function process_pending_reminders(): void {
        global $wpdb;

        $table = $wpdb->prefix . 'coh_reminders';
        $now   = current_time( 'mysql' );

        $reminders = $wpdb->get_results( $wpdb->prepare(
            "SELECT r.*, t.status as task_status
             FROM {$table} r
             LEFT JOIN {$wpdb->prefix}coh_tasks t ON r.task_id = t.id
             WHERE r.status = 'pending' AND r.scheduled_at <= %s
             ORDER BY r.scheduled_at ASC
             LIMIT 50",
            $now
        ), ARRAY_A );

        if ( empty( $reminders ) ) {
            return;
        }

        foreach ( $reminders as $reminder ) {
            // Skip if task is already completed.
            if ( in_array( $reminder['task_status'] ?? '', array( 'completed', 'skipped' ), true ) ) {
                $wpdb->update( $table, array( 'status' => 'cancelled' ), array( 'id' => $reminder['id'] ) );
                continue;
            }

            $sent = false;
            switch ( $reminder['channel'] ) {
                case 'email':
                    $sent = $this->send_email_reminder( $reminder );
                    break;
                case 'admin':
                    $sent = $this->queue_admin_notice( $reminder );
                    break;
                case 'slack':
                    $sent = $this->send_slack_reminder( $reminder );
                    break;
            }

            $wpdb->update(
                $table,
                array(
                    'status'  => $sent ? 'sent' : 'failed',
                    'sent_at' => $sent ? current_time( 'mysql' ) : null,
                ),
                array( 'id' => $reminder['id'] )
            );
        }
    }

    /**
     * Send an email reminder.
     */
    private function send_email_reminder( array $reminder ): bool {
        $settings   = get_option( 'coh_settings', array() );
        $recipients = $settings['reminder_email'] ?? get_option( 'admin_email' );

        if ( empty( $recipients ) ) {
            return false;
        }

        $subject = '[COH] ' . $reminder['subject'];
        $message = $reminder['message'];

        // Add link to task in admin.
        $task_url = admin_url( 'admin.php?page=coh-clients&client_id=' . $reminder['client_id'] );
        $message .= "\n\n---\nIm Dashboard oeffnen: " . $task_url;

        return wp_mail( $recipients, $subject, $message );
    }

    /**
     * Queue an admin notice.
     */
    private function queue_admin_notice( array $reminder ): bool {
        $notices   = get_transient( 'coh_admin_notices' ) ?: array();
        $notices[] = array(
            'type'      => 'warning',
            'message'   => $reminder['subject'],
            'client_id' => $reminder['client_id'],
            'task_id'   => $reminder['task_id'],
        );
        set_transient( 'coh_admin_notices', $notices, DAY_IN_SECONDS );
        return true;
    }

    /**
     * Send a Slack reminder.
     */
    private function send_slack_reminder( array $reminder ): bool {
        $api_key  = Api_Vault::get_key( 'slack' );
        $settings = get_option( 'coh_settings', array() );
        $channel  = $settings['slack_reminder_channel'] ?? $settings['slack_channel'] ?? '';

        if ( empty( $api_key ) || empty( $channel ) ) {
            return false;
        }

        $response = wp_remote_post( 'https://slack.com/api/chat.postMessage', array(
            'headers' => array(
                'Authorization' => 'Bearer ' . $api_key,
                'Content-Type'  => 'application/json',
            ),
            'body'    => wp_json_encode( array(
                'channel' => $channel,
                'text'    => ':bell: ' . $reminder['subject'] . "\n" . $reminder['message'],
            ) ),
            'timeout' => 10,
        ) );

        return ! is_wp_error( $response ) && 200 === wp_remote_retrieve_response_code( $response );
    }

    /**
     * Show admin notices for pending reminders.
     */
    public function show_admin_notices(): void {
        if ( ! current_user_can( 'coh_view_dashboard' ) ) {
            return;
        }

        $notices = get_transient( 'coh_admin_notices' );
        if ( empty( $notices ) || ! is_array( $notices ) ) {
            return;
        }

        foreach ( $notices as $notice ) {
            $url = admin_url( 'admin.php?page=coh-clients&client_id=' . ( $notice['client_id'] ?? '' ) );
            printf(
                '<div class="notice notice-%s is-dismissible"><p><strong>[Client Operations Hub]</strong> %s &mdash; <a href="%s">Details</a></p></div>',
                esc_attr( $notice['type'] ?? 'info' ),
                esc_html( $notice['message'] ),
                esc_url( $url )
            );
        }

        delete_transient( 'coh_admin_notices' );
    }

    /**
     * Daily check for overdue tasks — escalate.
     */
    public function check_overdue_tasks(): void {
        $overdue = Task_Engine::get_overdue_tasks();

        if ( empty( $overdue ) ) {
            return;
        }

        $settings   = get_option( 'coh_settings', array() );
        $recipients = $settings['escalation_email'] ?? $settings['reminder_email'] ?? get_option( 'admin_email' );

        $lines = array();
        foreach ( $overdue as $task ) {
            $days_overdue = (int) ( ( strtotime( current_time( 'Y-m-d' ) ) - strtotime( $task['due_date'] ) ) / 86400 );
            $lines[]      = sprintf(
                '- %s | %s | %d Tage ueberfaellig | Prioritaet: %s',
                $task['company_name'],
                $task['title'],
                $days_overdue,
                ucfirst( $task['priority'] )
            );
        }

        $subject = sprintf( '[COH] %d ueberfaellige Aufgaben', count( $overdue ) );
        $message = "Folgende Aufgaben sind ueberfaellig:\n\n" . implode( "\n", $lines );
        $message .= "\n\n---\nDashboard: " . admin_url( 'admin.php?page=coh-dashboard' );

        wp_mail( $recipients, $subject, $message );
    }

    /**
     * Get all reminders for a client.
     */
    public static function get_for_client( int $client_id, int $limit = 20 ): array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_reminders';

        return $wpdb->get_results( $wpdb->prepare(
            "SELECT * FROM {$table} WHERE client_id = %d ORDER BY scheduled_at DESC LIMIT %d",
            $client_id,
            $limit
        ), ARRAY_A ) ?: array();
    }
}
