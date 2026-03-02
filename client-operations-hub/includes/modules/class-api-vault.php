<?php
/**
 * Module A1: API Key Vault
 *
 * Encrypted storage, connection testing, and audit logging for API keys.
 *
 * @package ClientOperationsHub
 */

namespace COH\Modules;

use COH\Encryption;

defined( 'ABSPATH' ) || exit;

class Api_Vault {

    /**
     * Supported services with their test endpoints.
     */
    private const SERVICES = array(
        'hubspot'          => array(
            'label'    => 'HubSpot',
            'test_url' => 'https://api.hubapi.com/crm/v3/objects/contacts?limit=1',
            'auth'     => 'bearer',
        ),
        'clickup'          => array(
            'label'    => 'ClickUp',
            'test_url' => 'https://api.clickup.com/api/v2/user',
            'auth'     => 'bearer',
        ),
        'slack'            => array(
            'label'    => 'Slack (Bot Token)',
            'test_url' => 'https://slack.com/api/auth.test',
            'auth'     => 'bearer',
        ),
        'agencyanalytics'  => array(
            'label'    => 'AgencyAnalytics',
            'test_url' => 'https://api.agencyanalytics.com/v2/account',
            'auth'     => 'bearer',
        ),
        'activecampaign'   => array(
            'label'    => 'ActiveCampaign',
            'test_url' => '/api/3/users/me',
            'auth'     => 'api-token',
        ),
        'calendly'         => array(
            'label'    => 'Calendly',
            'test_url' => 'https://api.calendly.com/users/me',
            'auth'     => 'bearer',
        ),
    );

    /**
     * Get all stored API keys (decrypted key is NOT returned).
     */
    public static function get_all(): array {
        global $wpdb;
        $table   = $wpdb->prefix . 'coh_api_keys';
        $results = $wpdb->get_results( "SELECT id, service_name, service_label, status, last_tested, created_at, updated_at FROM {$table} ORDER BY service_name ASC", ARRAY_A );
        return $results ?: array();
    }

    /**
     * Get a single API key record.
     */
    public static function get( int $id ): ?array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_api_keys';
        $row   = $wpdb->get_row( $wpdb->prepare( "SELECT * FROM {$table} WHERE id = %d", $id ), ARRAY_A );
        return $row ?: null;
    }

    /**
     * Get the decrypted API key for a service.
     */
    public static function get_key( string $service_name ): string {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_api_keys';
        $row   = $wpdb->get_row(
            $wpdb->prepare( "SELECT api_key_encrypted, api_key_iv FROM {$table} WHERE service_name = %s", $service_name ),
            ARRAY_A
        );

        if ( ! $row ) {
            return '';
        }

        return Encryption::decrypt( $row['api_key_encrypted'], $row['api_key_iv'] );
    }

    /**
     * Get extra fields (e.g. base URL for ActiveCampaign) for a service.
     */
    public static function get_extra_fields( string $service_name ): array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_api_keys';
        $row   = $wpdb->get_row(
            $wpdb->prepare( "SELECT extra_fields FROM {$table} WHERE service_name = %s", $service_name ),
            ARRAY_A
        );

        if ( ! $row || empty( $row['extra_fields'] ) ) {
            return array();
        }

        return json_decode( $row['extra_fields'], true ) ?: array();
    }

    /**
     * Store or update an API key (encrypted).
     */
    public static function save( string $service_name, string $api_key, array $extra_fields = array() ): int {
        global $wpdb;

        $table     = $wpdb->prefix . 'coh_api_keys';
        $encrypted = Encryption::encrypt( $api_key );
        $label     = self::SERVICES[ $service_name ]['label'] ?? $service_name;
        $user_id   = get_current_user_id();

        $existing = $wpdb->get_var(
            $wpdb->prepare( "SELECT id FROM {$table} WHERE service_name = %s", $service_name )
        );

        $data = array(
            'service_name'      => $service_name,
            'service_label'     => $label,
            'api_key_encrypted' => $encrypted['encrypted'],
            'api_key_iv'        => $encrypted['iv'],
            'extra_fields'      => ! empty( $extra_fields ) ? wp_json_encode( $extra_fields ) : null,
            'status'            => 'untested',
        );

        if ( $existing ) {
            $wpdb->update( $table, $data, array( 'id' => $existing ) );
            $id = (int) $existing;
            self::audit_log( $id, 'updated', $user_id );
        } else {
            $data['created_by'] = $user_id;
            $wpdb->insert( $table, $data );
            $id = (int) $wpdb->insert_id;
            self::audit_log( $id, 'created', $user_id );
        }

        return $id;
    }

    /**
     * Delete an API key.
     */
    public static function delete( int $id ): bool {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_api_keys';

        self::audit_log( $id, 'deleted', get_current_user_id() );

        return (bool) $wpdb->delete( $table, array( 'id' => $id ) );
    }

    /**
     * Test connection for a stored service.
     */
    public static function test_connection( string $service_name ): array {
        $api_key = self::get_key( $service_name );
        if ( empty( $api_key ) ) {
            return array(
                'success' => false,
                'message' => 'Kein API-Key gespeichert.',
            );
        }

        $service = self::SERVICES[ $service_name ] ?? null;
        if ( ! $service ) {
            return array(
                'success' => false,
                'message' => 'Unbekannter Service.',
            );
        }

        $url     = $service['test_url'];
        $headers = array();

        // ActiveCampaign uses a different auth mechanism.
        if ( 'api-token' === $service['auth'] ) {
            $extra = self::get_extra_fields( $service_name );
            $base  = rtrim( $extra['base_url'] ?? '', '/' );
            if ( empty( $base ) ) {
                return array(
                    'success' => false,
                    'message' => 'Base-URL fehlt. Bitte in den Extra-Feldern konfigurieren.',
                );
            }
            $url                   = $base . $url;
            $headers['Api-Token']  = $api_key;
        } else {
            $headers['Authorization'] = 'Bearer ' . $api_key;
        }

        $response = wp_remote_get( $url, array(
            'headers' => $headers,
            'timeout' => 15,
        ) );

        if ( is_wp_error( $response ) ) {
            self::update_status( $service_name, 'error' );
            return array(
                'success' => false,
                'message' => $response->get_error_message(),
            );
        }

        $code = wp_remote_retrieve_response_code( $response );

        if ( $code >= 200 && $code < 300 ) {
            self::update_status( $service_name, 'connected' );
            return array(
                'success' => true,
                'message' => 'Verbindung erfolgreich (' . $code . ').',
            );
        }

        self::update_status( $service_name, 'error' );
        return array(
            'success' => false,
            'message' => 'HTTP ' . $code . ': ' . wp_remote_retrieve_body( $response ),
        );
    }

    /**
     * Update connection status.
     */
    private static function update_status( string $service_name, string $status ): void {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_api_keys';
        $wpdb->update(
            $table,
            array(
                'status'      => $status,
                'last_tested' => current_time( 'mysql' ),
            ),
            array( 'service_name' => $service_name )
        );
    }

    /**
     * Log an audit event.
     */
    private static function audit_log( int $api_key_id, string $action, int $user_id, string $details = '' ): void {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_api_key_audit';
        $wpdb->insert( $table, array(
            'api_key_id' => $api_key_id,
            'action'     => $action,
            'user_id'    => $user_id,
            'details'    => $details,
        ) );
    }

    /**
     * Get audit log entries.
     */
    public static function get_audit_log( int $limit = 50 ): array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_api_key_audit';
        $keys  = $wpdb->prefix . 'coh_api_keys';

        return $wpdb->get_results( $wpdb->prepare(
            "SELECT a.*, k.service_name, k.service_label, u.display_name
             FROM {$table} a
             LEFT JOIN {$keys} k ON a.api_key_id = k.id
             LEFT JOIN {$wpdb->users} u ON a.user_id = u.ID
             ORDER BY a.created_at DESC
             LIMIT %d",
            $limit
        ), ARRAY_A ) ?: array();
    }

    /**
     * Get list of supported services.
     */
    public static function get_supported_services(): array {
        return self::SERVICES;
    }
}
