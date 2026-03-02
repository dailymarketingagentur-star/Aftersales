<?php
/**
 * Module A2: Client Intake & Pipeline Router
 *
 * Handles new client creation, CRM integration, and task generation.
 *
 * @package ClientOperationsHub
 */

namespace COH\Modules;

defined( 'ABSPATH' ) || exit;

class Client_Intake {

    /**
     * Create a new client and trigger the full onboarding pipeline.
     *
     * @param array $data Client data.
     * @return int|false Client ID or false on failure.
     */
    public static function create_client( array $data ) {
        global $wpdb;

        $required = array( 'company_name', 'contact_name', 'email', 'start_date' );
        foreach ( $required as $field ) {
            if ( empty( $data[ $field ] ) ) {
                return false;
            }
        }

        $defaults = array(
            'phone'            => '',
            'website'          => '',
            'address'          => '',
            'package_type'     => '',
            'industry'         => '',
            'monthly_volume'   => 0,
            'tier'             => self::determine_tier( (float) ( $data['monthly_volume'] ?? 0 ) ),
            'health_score'     => 50,
            'status'           => 'active',
            'notes'            => '',
            'hubspot_deal_id'  => '',
            'clickup_project_id' => '',
        );

        $insert = wp_parse_args( $data, $defaults );
        $insert['tier'] = self::determine_tier( (float) $insert['monthly_volume'] );

        $table = $wpdb->prefix . 'coh_clients';
        $wpdb->insert( $table, $insert );
        $client_id = (int) $wpdb->insert_id;

        if ( ! $client_id ) {
            return false;
        }

        // Log activity.
        self::log_activity( $client_id, 'client_created', 'Neuer Kunde angelegt', sprintf(
            'Firma: %s, Paket: %s, Volumen: %s',
            $insert['company_name'],
            $insert['package_type'],
            number_format( (float) $insert['monthly_volume'], 2, ',', '.' )
        ) );

        // Generate tasks from templates.
        Task_Engine::generate_tasks_for_client( $client_id, $insert );

        // Try to create HubSpot deal.
        self::maybe_create_hubspot_deal( $client_id, $insert );

        // Try to create ClickUp project.
        self::maybe_create_clickup_project( $client_id, $insert );

        // Send Slack notification.
        self::maybe_notify_slack( $insert );

        return $client_id;
    }

    /**
     * Update an existing client.
     */
    public static function update_client( int $client_id, array $data ): bool {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_clients';

        // Recalculate tier if volume changed.
        if ( isset( $data['monthly_volume'] ) ) {
            $data['tier'] = self::determine_tier( (float) $data['monthly_volume'] );
        }

        $result = $wpdb->update( $table, $data, array( 'id' => $client_id ) );

        if ( $result !== false ) {
            self::log_activity( $client_id, 'client_updated', 'Kundendaten aktualisiert', wp_json_encode( array_keys( $data ) ) );
        }

        return $result !== false;
    }

    /**
     * Get a single client.
     */
    public static function get( int $client_id ): ?array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_clients';
        $row   = $wpdb->get_row( $wpdb->prepare( "SELECT * FROM {$table} WHERE id = %d", $client_id ), ARRAY_A );
        return $row ?: null;
    }

    /**
     * Get all clients with optional filters.
     */
    public static function get_all( array $filters = array() ): array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_clients';

        $where  = array( '1=1' );
        $values = array();

        if ( ! empty( $filters['status'] ) ) {
            $where[]  = 'status = %s';
            $values[] = $filters['status'];
        }

        if ( ! empty( $filters['tier'] ) ) {
            $where[]  = 'tier = %s';
            $values[] = $filters['tier'];
        }

        if ( ! empty( $filters['search'] ) ) {
            $like     = '%' . $wpdb->esc_like( $filters['search'] ) . '%';
            $where[]  = '(company_name LIKE %s OR contact_name LIKE %s OR email LIKE %s)';
            $values[] = $like;
            $values[] = $like;
            $values[] = $like;
        }

        $order = 'ORDER BY company_name ASC';
        if ( ! empty( $filters['orderby'] ) ) {
            $allowed = array( 'company_name', 'start_date', 'health_score', 'tier', 'created_at' );
            if ( in_array( $filters['orderby'], $allowed, true ) ) {
                $dir   = ( ! empty( $filters['order'] ) && 'DESC' === strtoupper( $filters['order'] ) ) ? 'DESC' : 'ASC';
                $order = "ORDER BY {$filters['orderby']} {$dir}";
            }
        }

        $where_sql = implode( ' AND ', $where );

        if ( ! empty( $values ) ) {
            $query = $wpdb->prepare( "SELECT * FROM {$table} WHERE {$where_sql} {$order}", ...$values );
        } else {
            $query = "SELECT * FROM {$table} WHERE {$where_sql} {$order}";
        }

        return $wpdb->get_results( $query, ARRAY_A ) ?: array();
    }

    /**
     * Delete a client and all associated data.
     */
    public static function delete_client( int $client_id ): bool {
        global $wpdb;

        // Delete tasks.
        $wpdb->delete( $wpdb->prefix . 'coh_tasks', array( 'client_id' => $client_id ) );
        // Delete activity log.
        $wpdb->delete( $wpdb->prefix . 'coh_activity_log', array( 'client_id' => $client_id ) );
        // Delete reminders.
        $wpdb->delete( $wpdb->prefix . 'coh_reminders', array( 'client_id' => $client_id ) );
        // Delete health history.
        $wpdb->delete( $wpdb->prefix . 'coh_health_history', array( 'client_id' => $client_id ) );
        // Delete client.
        return (bool) $wpdb->delete( $wpdb->prefix . 'coh_clients', array( 'id' => $client_id ) );
    }

    /**
     * Determine tier based on monthly volume.
     */
    public static function determine_tier( float $volume ): string {
        if ( $volume >= 10000 ) {
            return 'platin';
        }
        if ( $volume >= 5000 ) {
            return 'gold';
        }
        if ( $volume >= 2000 ) {
            return 'silber';
        }
        return 'bronze';
    }

    /**
     * Log an activity entry for a client.
     */
    public static function log_activity( int $client_id, string $type, string $title, string $description = '', array $meta = array() ): void {
        global $wpdb;
        $wpdb->insert( $wpdb->prefix . 'coh_activity_log', array(
            'client_id'     => $client_id,
            'activity_type' => $type,
            'title'         => $title,
            'description'   => $description,
            'meta'          => ! empty( $meta ) ? wp_json_encode( $meta ) : null,
            'user_id'       => get_current_user_id(),
        ) );
    }

    /**
     * Get activity log for a client.
     */
    public static function get_activity_log( int $client_id, int $limit = 50 ): array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_activity_log';
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT a.*, u.display_name
             FROM {$table} a
             LEFT JOIN {$wpdb->users} u ON a.user_id = u.ID
             WHERE a.client_id = %d
             ORDER BY a.created_at DESC
             LIMIT %d",
            $client_id,
            $limit
        ), ARRAY_A ) ?: array();
    }

    /**
     * Try to create a HubSpot deal via API.
     */
    private static function maybe_create_hubspot_deal( int $client_id, array $client ): void {
        $api_key = Api_Vault::get_key( 'hubspot' );
        if ( empty( $api_key ) ) {
            return;
        }

        $response = wp_remote_post( 'https://api.hubapi.com/crm/v3/objects/deals', array(
            'headers' => array(
                'Authorization' => 'Bearer ' . $api_key,
                'Content-Type'  => 'application/json',
            ),
            'body'    => wp_json_encode( array(
                'properties' => array(
                    'dealname'    => $client['company_name'] . ' - ' . $client['package_type'],
                    'amount'      => $client['monthly_volume'],
                    'dealstage'   => 'closedwon',
                    'pipeline'    => 'default',
                ),
            ) ),
            'timeout' => 15,
        ) );

        if ( ! is_wp_error( $response ) ) {
            $body = json_decode( wp_remote_retrieve_body( $response ), true );
            if ( ! empty( $body['id'] ) ) {
                global $wpdb;
                $wpdb->update(
                    $wpdb->prefix . 'coh_clients',
                    array( 'hubspot_deal_id' => $body['id'] ),
                    array( 'id' => $client_id )
                );
                self::log_activity( $client_id, 'hubspot_deal_created', 'HubSpot Deal erstellt', 'Deal ID: ' . $body['id'] );
            }
        }
    }

    /**
     * Try to create a ClickUp project via API.
     */
    private static function maybe_create_clickup_project( int $client_id, array $client ): void {
        $api_key = Api_Vault::get_key( 'clickup' );
        if ( empty( $api_key ) ) {
            return;
        }

        $settings = get_option( 'coh_settings', array() );
        $list_id  = $settings['clickup_list_id'] ?? '';
        if ( empty( $list_id ) ) {
            return;
        }

        $response = wp_remote_post( "https://api.clickup.com/api/v2/list/{$list_id}/task", array(
            'headers' => array(
                'Authorization' => $api_key,
                'Content-Type'  => 'application/json',
            ),
            'body'    => wp_json_encode( array(
                'name'        => $client['company_name'] . ' - Onboarding',
                'description' => sprintf( 'Paket: %s | Branche: %s | Volumen: %s', $client['package_type'], $client['industry'], $client['monthly_volume'] ),
            ) ),
            'timeout' => 15,
        ) );

        if ( ! is_wp_error( $response ) ) {
            $body = json_decode( wp_remote_retrieve_body( $response ), true );
            if ( ! empty( $body['id'] ) ) {
                global $wpdb;
                $wpdb->update(
                    $wpdb->prefix . 'coh_clients',
                    array( 'clickup_project_id' => $body['id'] ),
                    array( 'id' => $client_id )
                );
                self::log_activity( $client_id, 'clickup_project_created', 'ClickUp Projekt erstellt', 'Task ID: ' . $body['id'] );
            }
        }
    }

    /**
     * Send Slack notification for new client.
     */
    private static function maybe_notify_slack( array $client ): void {
        $api_key = Api_Vault::get_key( 'slack' );
        if ( empty( $api_key ) ) {
            return;
        }

        $settings = get_option( 'coh_settings', array() );
        $channel  = $settings['slack_channel'] ?? '';
        if ( empty( $channel ) ) {
            return;
        }

        $text = sprintf(
            ":tada: *Neuer Kunde!*\n*Firma:* %s\n*Kontakt:* %s\n*Paket:* %s\n*Volumen:* %s EUR/Monat\n*Tier:* %s",
            $client['company_name'],
            $client['contact_name'],
            $client['package_type'],
            number_format( (float) $client['monthly_volume'], 0, ',', '.' ),
            ucfirst( self::determine_tier( (float) $client['monthly_volume'] ) )
        );

        wp_remote_post( 'https://slack.com/api/chat.postMessage', array(
            'headers' => array(
                'Authorization' => 'Bearer ' . $api_key,
                'Content-Type'  => 'application/json',
            ),
            'body'    => wp_json_encode( array(
                'channel' => $channel,
                'text'    => $text,
            ) ),
            'timeout' => 10,
        ) );
    }

    /**
     * Handle incoming webhook for new client (public endpoint).
     */
    public static function handle_webhook( \WP_REST_Request $request ): \WP_REST_Response {
        $params = $request->get_json_params();

        if ( empty( $params ) ) {
            $params = $request->get_params();
        }

        $secret   = $request->get_header( 'X-COH-Secret' );
        $settings = get_option( 'coh_settings', array() );

        if ( ! empty( $settings['webhook_secret'] ) && $secret !== $settings['webhook_secret'] ) {
            return new \WP_REST_Response( array( 'error' => 'Unauthorized' ), 401 );
        }

        $client_id = self::create_client( array(
            'company_name'   => sanitize_text_field( $params['company_name'] ?? '' ),
            'contact_name'   => sanitize_text_field( $params['contact_name'] ?? '' ),
            'email'          => sanitize_email( $params['email'] ?? '' ),
            'phone'          => sanitize_text_field( $params['phone'] ?? '' ),
            'website'        => esc_url_raw( $params['website'] ?? '' ),
            'address'        => sanitize_textarea_field( $params['address'] ?? '' ),
            'package_type'   => sanitize_text_field( $params['package_type'] ?? '' ),
            'industry'       => sanitize_text_field( $params['industry'] ?? '' ),
            'monthly_volume' => (float) ( $params['monthly_volume'] ?? 0 ),
            'start_date'     => sanitize_text_field( $params['start_date'] ?? current_time( 'Y-m-d' ) ),
            'notes'          => sanitize_textarea_field( $params['notes'] ?? '' ),
        ) );

        if ( ! $client_id ) {
            return new \WP_REST_Response( array( 'error' => 'Pflichtfelder fehlen (company_name, contact_name, email, start_date).' ), 400 );
        }

        return new \WP_REST_Response( array(
            'success'   => true,
            'client_id' => $client_id,
        ), 201 );
    }
}
