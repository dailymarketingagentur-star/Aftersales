<?php
/**
 * Module A3: Task Engine (Aufgaben-Engine)
 *
 * Generates and manages tasks per client based on the 11-phase process.
 *
 * @package ClientOperationsHub
 */

namespace COH\Modules;

use COH\Task_Templates;

defined( 'ABSPATH' ) || exit;

class Task_Engine {

    /**
     * Generate all tasks for a new client from templates.
     *
     * @param int   $client_id Client ID.
     * @param array $client    Client data (for conditional template filtering).
     */
    public static function generate_tasks_for_client( int $client_id, array $client ): void {
        global $wpdb;

        $context   = array(
            'package_type'   => $client['package_type'] ?? '',
            'monthly_volume' => (float) ( $client['monthly_volume'] ?? 0 ),
            'tier'           => $client['tier'] ?? 'bronze',
            'industry'       => $client['industry'] ?? '',
        );
        $templates = Task_Templates::get_templates( $context );
        $start     = $client['start_date'] ?? current_time( 'Y-m-d' );
        $table     = $wpdb->prefix . 'coh_tasks';

        foreach ( $templates as $tpl ) {
            $due_date = gmdate( 'Y-m-d', strtotime( $start . ' + ' . (int) $tpl['day_offset'] . ' days' ) );

            $wpdb->insert( $table, array(
                'client_id'   => $client_id,
                'template_id' => $tpl['id'],
                'title'       => $tpl['title'],
                'description' => $tpl['description'],
                'task_type'   => $tpl['task_type'],
                'due_date'    => $due_date,
                'priority'    => $tpl['priority'],
                'status'      => 'pending',
                'phase'       => $tpl['phase'],
                'sort_order'  => $tpl['sort_order'],
            ) );

            $task_id = (int) $wpdb->insert_id;

            // Create a reminder for the day the task is due.
            Reminder::schedule_for_task( $task_id, $client_id, $due_date );
        }

        Client_Intake::log_activity(
            $client_id,
            'tasks_generated',
            'Aufgaben generiert',
            sprintf( '%d Aufgaben aus dem 11-Phasen-Prozess erstellt.', count( $templates ) )
        );
    }

    /**
     * Get tasks for a client.
     */
    public static function get_tasks( int $client_id, array $filters = array() ): array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_tasks';

        $where  = array( 'client_id = %d' );
        $values = array( $client_id );

        if ( ! empty( $filters['status'] ) ) {
            $where[]  = 'status = %s';
            $values[] = $filters['status'];
        }

        if ( ! empty( $filters['phase'] ) ) {
            $where[]  = 'phase = %d';
            $values[] = (int) $filters['phase'];
        }

        if ( ! empty( $filters['assigned_to'] ) ) {
            $where[]  = 'assigned_to = %d';
            $values[] = (int) $filters['assigned_to'];
        }

        $where_sql = implode( ' AND ', $where );
        $order     = 'ORDER BY due_date ASC, sort_order ASC';

        return $wpdb->get_results(
            $wpdb->prepare( "SELECT * FROM {$table} WHERE {$where_sql} {$order}", ...$values ),
            ARRAY_A
        ) ?: array();
    }

    /**
     * Get a single task.
     */
    public static function get_task( int $task_id ): ?array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_tasks';
        $row   = $wpdb->get_row( $wpdb->prepare( "SELECT * FROM {$table} WHERE id = %d", $task_id ), ARRAY_A );
        return $row ?: null;
    }

    /**
     * Update a task.
     */
    public static function update_task( int $task_id, array $data ): bool {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_tasks';

        if ( isset( $data['status'] ) && 'completed' === $data['status'] ) {
            $data['completed_at'] = current_time( 'mysql' );
            $data['completed_by'] = get_current_user_id();
        }

        $result = $wpdb->update( $table, $data, array( 'id' => $task_id ) );

        if ( $result !== false ) {
            $task = self::get_task( $task_id );
            if ( $task ) {
                $log_title = isset( $data['status'] ) ? 'Aufgabe: ' . $data['status'] : 'Aufgabe aktualisiert';
                Client_Intake::log_activity(
                    (int) $task['client_id'],
                    'task_updated',
                    $log_title,
                    $task['title']
                );
            }
        }

        return $result !== false;
    }

    /**
     * Complete a task.
     */
    public static function complete_task( int $task_id, string $notes = '' ): bool {
        $data = array( 'status' => 'completed' );
        if ( $notes ) {
            $data['notes'] = $notes;
        }
        return self::update_task( $task_id, $data );
    }

    /**
     * Skip a task.
     */
    public static function skip_task( int $task_id, string $reason = '' ): bool {
        return self::update_task( $task_id, array(
            'status' => 'skipped',
            'notes'  => $reason,
        ) );
    }

    /**
     * Get all tasks due today across all clients.
     */
    public static function get_tasks_due_today(): array {
        global $wpdb;
        $table   = $wpdb->prefix . 'coh_tasks';
        $clients = $wpdb->prefix . 'coh_clients';
        $today   = current_time( 'Y-m-d' );

        return $wpdb->get_results( $wpdb->prepare(
            "SELECT t.*, c.company_name, c.contact_name, c.tier
             FROM {$table} t
             JOIN {$clients} c ON t.client_id = c.id
             WHERE t.due_date = %s AND t.status IN ('pending', 'in_progress')
             ORDER BY t.priority = 'high' DESC, t.sort_order ASC",
            $today
        ), ARRAY_A ) ?: array();
    }

    /**
     * Get all overdue tasks.
     */
    public static function get_overdue_tasks(): array {
        global $wpdb;
        $table   = $wpdb->prefix . 'coh_tasks';
        $clients = $wpdb->prefix . 'coh_clients';
        $today   = current_time( 'Y-m-d' );

        return $wpdb->get_results( $wpdb->prepare(
            "SELECT t.*, c.company_name, c.contact_name, c.tier
             FROM {$table} t
             JOIN {$clients} c ON t.client_id = c.id
             WHERE t.due_date < %s AND t.status IN ('pending', 'in_progress')
             ORDER BY t.due_date ASC, t.priority = 'high' DESC",
            $today
        ), ARRAY_A ) ?: array();
    }

    /**
     * Get tasks for the upcoming week.
     */
    public static function get_tasks_upcoming_week(): array {
        global $wpdb;
        $table   = $wpdb->prefix . 'coh_tasks';
        $clients = $wpdb->prefix . 'coh_clients';
        $today   = current_time( 'Y-m-d' );
        $week    = gmdate( 'Y-m-d', strtotime( $today . ' + 7 days' ) );

        return $wpdb->get_results( $wpdb->prepare(
            "SELECT t.*, c.company_name, c.contact_name, c.tier
             FROM {$table} t
             JOIN {$clients} c ON t.client_id = c.id
             WHERE t.due_date BETWEEN %s AND %s AND t.status IN ('pending', 'in_progress')
             ORDER BY t.due_date ASC, t.sort_order ASC",
            $today,
            $week
        ), ARRAY_A ) ?: array();
    }

    /**
     * Get task statistics for the dashboard.
     */
    public static function get_stats(): array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_tasks';
        $today = current_time( 'Y-m-d' );

        $total     = (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$table}" );
        $pending   = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$table} WHERE status = %s", 'pending' ) );
        $completed = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$table} WHERE status = %s", 'completed' ) );
        $overdue   = (int) $wpdb->get_var( $wpdb->prepare(
            "SELECT COUNT(*) FROM {$table} WHERE due_date < %s AND status IN ('pending', 'in_progress')",
            $today
        ) );
        $due_today = (int) $wpdb->get_var( $wpdb->prepare(
            "SELECT COUNT(*) FROM {$table} WHERE due_date = %s AND status IN ('pending', 'in_progress')",
            $today
        ) );

        return array(
            'total'           => $total,
            'pending'         => $pending,
            'completed'       => $completed,
            'overdue'         => $overdue,
            'due_today'       => $due_today,
            'completion_rate' => $total > 0 ? round( ( $completed / $total ) * 100, 1 ) : 0,
        );
    }

    /**
     * Get the next pending task for a client.
     */
    public static function get_next_task( int $client_id ): ?array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_tasks';
        $row   = $wpdb->get_row( $wpdb->prepare(
            "SELECT * FROM {$table} WHERE client_id = %d AND status IN ('pending', 'in_progress') ORDER BY due_date ASC, sort_order ASC LIMIT 1",
            $client_id
        ), ARRAY_A );
        return $row ?: null;
    }

    /**
     * Get the current phase of a client based on completed tasks.
     */
    public static function get_current_phase( int $client_id ): int {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_tasks';

        $last_completed_phase = (int) $wpdb->get_var( $wpdb->prepare(
            "SELECT MAX(phase) FROM {$table} WHERE client_id = %d AND status = 'completed'",
            $client_id
        ) );

        $first_pending_phase = (int) $wpdb->get_var( $wpdb->prepare(
            "SELECT MIN(phase) FROM {$table} WHERE client_id = %d AND status IN ('pending', 'in_progress')",
            $client_id
        ) );

        return $first_pending_phase ?: $last_completed_phase ?: 1;
    }
}
