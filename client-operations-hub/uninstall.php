<?php
/**
 * Uninstall: remove all plugin data.
 *
 * @package ClientOperationsHub
 */

defined( 'WP_UNINSTALL_PLUGIN' ) || exit;

global $wpdb;

// Remove custom tables.
$tables = array(
    $wpdb->prefix . 'coh_clients',
    $wpdb->prefix . 'coh_tasks',
    $wpdb->prefix . 'coh_task_templates',
    $wpdb->prefix . 'coh_api_keys',
    $wpdb->prefix . 'coh_api_key_audit',
    $wpdb->prefix . 'coh_activity_log',
    $wpdb->prefix . 'coh_reminders',
    $wpdb->prefix . 'coh_health_history',
);

foreach ( $tables as $table ) {
    $wpdb->query( "DROP TABLE IF EXISTS {$table}" ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
}

// Remove options.
delete_option( 'coh_version' );
delete_option( 'coh_settings' );
delete_option( 'coh_encryption_key' );

// Remove capabilities.
$admin = get_role( 'administrator' );
if ( $admin ) {
    $caps = array(
        'coh_manage_clients',
        'coh_manage_tasks',
        'coh_manage_api_keys',
        'coh_view_dashboard',
        'coh_manage_settings',
    );
    foreach ( $caps as $cap ) {
        $admin->remove_cap( $cap );
    }
}
