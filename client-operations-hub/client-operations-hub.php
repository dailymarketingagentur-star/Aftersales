<?php
/**
 * Plugin Name: Client Operations Hub
 * Plugin URI:  https://example.com/client-operations-hub
 * Description: Zentrale Schaltstelle fuer den 11-Phasen After-Sales-Prozess. Verwaltet Kunden, Aufgaben, Erinnerungen und Integrationen.
 * Version:     1.0.0
 * Author:      Agentur
 * Text Domain: client-operations-hub
 * Domain Path: /languages
 * Requires at least: 6.0
 * Requires PHP: 8.0
 *
 * @package ClientOperationsHub
 */

defined( 'ABSPATH' ) || exit;

define( 'COH_VERSION', '1.0.0' );
define( 'COH_PLUGIN_DIR', plugin_dir_path( __FILE__ ) );
define( 'COH_PLUGIN_URL', plugin_dir_url( __FILE__ ) );
define( 'COH_PLUGIN_BASENAME', plugin_basename( __FILE__ ) );

/**
 * Autoloader for plugin classes.
 */
spl_autoload_register( function ( $class ) {
    $prefix    = 'COH\\';
    $base_dirs = array(
        COH_PLUGIN_DIR . 'includes/',
        COH_PLUGIN_DIR . 'includes/modules/',
        COH_PLUGIN_DIR . 'admin/',
    );

    if ( strpos( $class, $prefix ) !== 0 ) {
        return;
    }

    $relative_class = substr( $class, strlen( $prefix ) );
    $file_name      = 'class-' . strtolower( str_replace( array( '_', '\\' ), array( '-', '/' ), $relative_class ) ) . '.php';

    foreach ( $base_dirs as $base_dir ) {
        $file = $base_dir . $file_name;
        if ( file_exists( $file ) ) {
            require_once $file;
            return;
        }
    }
} );

/**
 * Plugin activation.
 */
function coh_activate() {
    require_once COH_PLUGIN_DIR . 'includes/class-activator.php';
    COH\Activator::activate();
}
register_activation_hook( __FILE__, 'coh_activate' );

/**
 * Plugin deactivation.
 */
function coh_deactivate() {
    require_once COH_PLUGIN_DIR . 'includes/class-deactivator.php';
    COH\Deactivator::deactivate();
}
register_deactivation_hook( __FILE__, 'coh_deactivate' );

/**
 * Boot the plugin after all plugins are loaded.
 */
add_action( 'plugins_loaded', function () {
    require_once COH_PLUGIN_DIR . 'includes/class-encryption.php';
    require_once COH_PLUGIN_DIR . 'includes/class-rest-api.php';
    require_once COH_PLUGIN_DIR . 'includes/modules/class-api-vault.php';
    require_once COH_PLUGIN_DIR . 'includes/modules/class-client-intake.php';
    require_once COH_PLUGIN_DIR . 'includes/modules/class-task-engine.php';
    require_once COH_PLUGIN_DIR . 'includes/modules/class-dashboard.php';
    require_once COH_PLUGIN_DIR . 'includes/modules/class-reminder.php';
    require_once COH_PLUGIN_DIR . 'includes/class-task-templates.php';

    if ( is_admin() ) {
        require_once COH_PLUGIN_DIR . 'admin/class-admin.php';
        $admin = new COH\Admin();
        $admin->init();
    }

    $rest_api = new COH\Rest_API();
    $rest_api->init();

    $reminder = new COH\Modules\Reminder();
    $reminder->init();
} );
