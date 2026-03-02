<?php
/**
 * REST API endpoints for AJAX operations.
 *
 * @package ClientOperationsHub
 */

namespace COH;

use COH\Modules\Api_Vault;
use COH\Modules\Client_Intake;
use COH\Modules\Task_Engine;
use COH\Modules\Dashboard;

defined( 'ABSPATH' ) || exit;

class Rest_API {

    private const NAMESPACE = 'coh/v1';

    public function init(): void {
        add_action( 'rest_api_init', array( $this, 'register_routes' ) );
    }

    public function register_routes(): void {

        // --- Dashboard ---
        register_rest_route( self::NAMESPACE, '/dashboard', array(
            'methods'             => 'GET',
            'callback'            => array( $this, 'get_dashboard' ),
            'permission_callback' => array( $this, 'can_view' ),
        ) );

        // --- Clients ---
        register_rest_route( self::NAMESPACE, '/clients', array(
            array(
                'methods'             => 'GET',
                'callback'            => array( $this, 'get_clients' ),
                'permission_callback' => array( $this, 'can_manage_clients' ),
            ),
            array(
                'methods'             => 'POST',
                'callback'            => array( $this, 'create_client' ),
                'permission_callback' => array( $this, 'can_manage_clients' ),
            ),
        ) );

        register_rest_route( self::NAMESPACE, '/clients/(?P<id>\d+)', array(
            array(
                'methods'             => 'GET',
                'callback'            => array( $this, 'get_client' ),
                'permission_callback' => array( $this, 'can_manage_clients' ),
            ),
            array(
                'methods'             => 'PUT',
                'callback'            => array( $this, 'update_client' ),
                'permission_callback' => array( $this, 'can_manage_clients' ),
            ),
            array(
                'methods'             => 'DELETE',
                'callback'            => array( $this, 'delete_client' ),
                'permission_callback' => array( $this, 'can_manage_clients' ),
            ),
        ) );

        register_rest_route( self::NAMESPACE, '/clients/(?P<id>\d+)/activity', array(
            'methods'             => 'GET',
            'callback'            => array( $this, 'get_client_activity' ),
            'permission_callback' => array( $this, 'can_manage_clients' ),
        ) );

        register_rest_route( self::NAMESPACE, '/clients/(?P<id>\d+)/activity', array(
            'methods'             => 'POST',
            'callback'            => array( $this, 'add_client_note' ),
            'permission_callback' => array( $this, 'can_manage_clients' ),
        ) );

        // --- Tasks ---
        register_rest_route( self::NAMESPACE, '/clients/(?P<client_id>\d+)/tasks', array(
            'methods'             => 'GET',
            'callback'            => array( $this, 'get_tasks' ),
            'permission_callback' => array( $this, 'can_manage_tasks' ),
        ) );

        register_rest_route( self::NAMESPACE, '/tasks/(?P<id>\d+)', array(
            array(
                'methods'             => 'PUT',
                'callback'            => array( $this, 'update_task' ),
                'permission_callback' => array( $this, 'can_manage_tasks' ),
            ),
        ) );

        register_rest_route( self::NAMESPACE, '/tasks/(?P<id>\d+)/complete', array(
            'methods'             => 'POST',
            'callback'            => array( $this, 'complete_task' ),
            'permission_callback' => array( $this, 'can_manage_tasks' ),
        ) );

        register_rest_route( self::NAMESPACE, '/tasks/(?P<id>\d+)/skip', array(
            'methods'             => 'POST',
            'callback'            => array( $this, 'skip_task' ),
            'permission_callback' => array( $this, 'can_manage_tasks' ),
        ) );

        // --- API Vault ---
        register_rest_route( self::NAMESPACE, '/api-keys', array(
            array(
                'methods'             => 'GET',
                'callback'            => array( $this, 'get_api_keys' ),
                'permission_callback' => array( $this, 'can_manage_api_keys' ),
            ),
        ) );

        register_rest_route( self::NAMESPACE, '/api-keys/(?P<service>[a-z_]+)', array(
            array(
                'methods'             => 'POST',
                'callback'            => array( $this, 'save_api_key' ),
                'permission_callback' => array( $this, 'can_manage_api_keys' ),
            ),
            array(
                'methods'             => 'DELETE',
                'callback'            => array( $this, 'delete_api_key' ),
                'permission_callback' => array( $this, 'can_manage_api_keys' ),
            ),
        ) );

        register_rest_route( self::NAMESPACE, '/api-keys/(?P<service>[a-z_]+)/test', array(
            'methods'             => 'POST',
            'callback'            => array( $this, 'test_api_key' ),
            'permission_callback' => array( $this, 'can_manage_api_keys' ),
        ) );

        // --- Public Webhook ---
        register_rest_route( self::NAMESPACE, '/webhook/new-client', array(
            'methods'             => 'POST',
            'callback'            => array( Client_Intake::class, 'handle_webhook' ),
            'permission_callback' => '__return_true',
        ) );
    }

    // =========================================================================
    // Permission callbacks
    // =========================================================================

    public function can_view(): bool {
        return current_user_can( 'coh_view_dashboard' );
    }

    public function can_manage_clients(): bool {
        return current_user_can( 'coh_manage_clients' );
    }

    public function can_manage_tasks(): bool {
        return current_user_can( 'coh_manage_tasks' );
    }

    public function can_manage_api_keys(): bool {
        return current_user_can( 'coh_manage_api_keys' );
    }

    // =========================================================================
    // Dashboard
    // =========================================================================

    public function get_dashboard(): \WP_REST_Response {
        return new \WP_REST_Response( Dashboard::get_dashboard_data() );
    }

    // =========================================================================
    // Clients
    // =========================================================================

    public function get_clients( \WP_REST_Request $request ): \WP_REST_Response {
        $filters = array(
            'status'  => $request->get_param( 'status' ),
            'tier'    => $request->get_param( 'tier' ),
            'search'  => $request->get_param( 'search' ),
            'orderby' => $request->get_param( 'orderby' ),
            'order'   => $request->get_param( 'order' ),
        );
        return new \WP_REST_Response( Client_Intake::get_all( array_filter( $filters ) ) );
    }

    public function get_client( \WP_REST_Request $request ): \WP_REST_Response {
        $client = Client_Intake::get( (int) $request['id'] );
        if ( ! $client ) {
            return new \WP_REST_Response( array( 'error' => 'Kunde nicht gefunden.' ), 404 );
        }

        $client['phase']     = Task_Engine::get_current_phase( (int) $client['id'] );
        $client['next_task'] = Task_Engine::get_next_task( (int) $client['id'] );

        return new \WP_REST_Response( $client );
    }

    public function create_client( \WP_REST_Request $request ): \WP_REST_Response {
        $params    = $request->get_json_params();
        $client_id = Client_Intake::create_client( array(
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
            return new \WP_REST_Response( array( 'error' => 'Pflichtfelder fehlen.' ), 400 );
        }

        return new \WP_REST_Response( array( 'success' => true, 'client_id' => $client_id ), 201 );
    }

    public function update_client( \WP_REST_Request $request ): \WP_REST_Response {
        $params   = $request->get_json_params();
        $sanitized = array();

        $text_fields = array( 'company_name', 'contact_name', 'phone', 'package_type', 'industry', 'status' );
        foreach ( $text_fields as $field ) {
            if ( isset( $params[ $field ] ) ) {
                $sanitized[ $field ] = sanitize_text_field( $params[ $field ] );
            }
        }
        if ( isset( $params['email'] ) ) {
            $sanitized['email'] = sanitize_email( $params['email'] );
        }
        if ( isset( $params['website'] ) ) {
            $sanitized['website'] = esc_url_raw( $params['website'] );
        }
        if ( isset( $params['address'] ) ) {
            $sanitized['address'] = sanitize_textarea_field( $params['address'] );
        }
        if ( isset( $params['monthly_volume'] ) ) {
            $sanitized['monthly_volume'] = (float) $params['monthly_volume'];
        }
        if ( isset( $params['health_score'] ) ) {
            $sanitized['health_score'] = max( 0, min( 100, (int) $params['health_score'] ) );
        }
        if ( isset( $params['notes'] ) ) {
            $sanitized['notes'] = sanitize_textarea_field( $params['notes'] );
        }

        $ok = Client_Intake::update_client( (int) $request['id'], $sanitized );
        return new \WP_REST_Response( array( 'success' => $ok ) );
    }

    public function delete_client( \WP_REST_Request $request ): \WP_REST_Response {
        $ok = Client_Intake::delete_client( (int) $request['id'] );
        return new \WP_REST_Response( array( 'success' => $ok ) );
    }

    public function get_client_activity( \WP_REST_Request $request ): \WP_REST_Response {
        return new \WP_REST_Response( Client_Intake::get_activity_log( (int) $request['id'] ) );
    }

    public function add_client_note( \WP_REST_Request $request ): \WP_REST_Response {
        $params = $request->get_json_params();
        Client_Intake::log_activity(
            (int) $request['id'],
            'note',
            sanitize_text_field( $params['title'] ?? 'Notiz' ),
            sanitize_textarea_field( $params['description'] ?? '' )
        );
        return new \WP_REST_Response( array( 'success' => true ), 201 );
    }

    // =========================================================================
    // Tasks
    // =========================================================================

    public function get_tasks( \WP_REST_Request $request ): \WP_REST_Response {
        $filters = array_filter( array(
            'status'      => $request->get_param( 'status' ),
            'phase'       => $request->get_param( 'phase' ),
            'assigned_to' => $request->get_param( 'assigned_to' ),
        ) );
        return new \WP_REST_Response( Task_Engine::get_tasks( (int) $request['client_id'], $filters ) );
    }

    public function update_task( \WP_REST_Request $request ): \WP_REST_Response {
        $params    = $request->get_json_params();
        $sanitized = array();

        if ( isset( $params['status'] ) ) {
            $sanitized['status'] = sanitize_text_field( $params['status'] );
        }
        if ( isset( $params['assigned_to'] ) ) {
            $sanitized['assigned_to'] = (int) $params['assigned_to'];
        }
        if ( isset( $params['notes'] ) ) {
            $sanitized['notes'] = sanitize_textarea_field( $params['notes'] );
        }
        if ( isset( $params['due_date'] ) ) {
            $sanitized['due_date'] = sanitize_text_field( $params['due_date'] );
        }

        $ok = Task_Engine::update_task( (int) $request['id'], $sanitized );
        return new \WP_REST_Response( array( 'success' => $ok ) );
    }

    public function complete_task( \WP_REST_Request $request ): \WP_REST_Response {
        $params = $request->get_json_params();
        $notes  = sanitize_textarea_field( $params['notes'] ?? '' );
        $ok     = Task_Engine::complete_task( (int) $request['id'], $notes );
        return new \WP_REST_Response( array( 'success' => $ok ) );
    }

    public function skip_task( \WP_REST_Request $request ): \WP_REST_Response {
        $params = $request->get_json_params();
        $reason = sanitize_textarea_field( $params['reason'] ?? '' );
        $ok     = Task_Engine::skip_task( (int) $request['id'], $reason );
        return new \WP_REST_Response( array( 'success' => $ok ) );
    }

    // =========================================================================
    // API Vault
    // =========================================================================

    public function get_api_keys(): \WP_REST_Response {
        return new \WP_REST_Response( Api_Vault::get_all() );
    }

    public function save_api_key( \WP_REST_Request $request ): \WP_REST_Response {
        $params  = $request->get_json_params();
        $service = sanitize_text_field( $request['service'] );
        $api_key = $params['api_key'] ?? '';

        if ( empty( $api_key ) ) {
            return new \WP_REST_Response( array( 'error' => 'API-Key darf nicht leer sein.' ), 400 );
        }

        $extra = array();
        if ( ! empty( $params['base_url'] ) ) {
            $extra['base_url'] = esc_url_raw( $params['base_url'] );
        }

        $id = Api_Vault::save( $service, $api_key, $extra );
        return new \WP_REST_Response( array( 'success' => true, 'id' => $id ), 201 );
    }

    public function delete_api_key( \WP_REST_Request $request ): \WP_REST_Response {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_api_keys';
        $row   = $wpdb->get_row( $wpdb->prepare(
            "SELECT id FROM {$table} WHERE service_name = %s",
            sanitize_text_field( $request['service'] )
        ) );

        if ( ! $row ) {
            return new \WP_REST_Response( array( 'error' => 'Nicht gefunden.' ), 404 );
        }

        $ok = Api_Vault::delete( (int) $row->id );
        return new \WP_REST_Response( array( 'success' => $ok ) );
    }

    public function test_api_key( \WP_REST_Request $request ): \WP_REST_Response {
        $result = Api_Vault::test_connection( sanitize_text_field( $request['service'] ) );
        return new \WP_REST_Response( $result );
    }
}
