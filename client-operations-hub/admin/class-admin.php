<?php
/**
 * Admin menu registration, asset loading, and page routing.
 *
 * @package ClientOperationsHub
 */

namespace COH;

defined( 'ABSPATH' ) || exit;

class Admin {

    public function init(): void {
        add_action( 'admin_menu', array( $this, 'register_menus' ) );
        add_action( 'admin_enqueue_scripts', array( $this, 'enqueue_assets' ) );
    }

    /**
     * Register admin menu pages.
     */
    public function register_menus(): void {
        add_menu_page(
            'Client Operations Hub',
            'Operations Hub',
            'coh_view_dashboard',
            'coh-dashboard',
            array( $this, 'render_dashboard' ),
            'dashicons-businessman',
            3
        );

        add_submenu_page(
            'coh-dashboard',
            'Dashboard',
            'Dashboard',
            'coh_view_dashboard',
            'coh-dashboard',
            array( $this, 'render_dashboard' )
        );

        add_submenu_page(
            'coh-dashboard',
            'Kunden',
            'Kunden',
            'coh_manage_clients',
            'coh-clients',
            array( $this, 'render_clients' )
        );

        add_submenu_page(
            'coh-dashboard',
            'API-Schluessel',
            'API-Schluessel',
            'coh_manage_api_keys',
            'coh-api-vault',
            array( $this, 'render_api_vault' )
        );

        add_submenu_page(
            'coh-dashboard',
            'Einstellungen',
            'Einstellungen',
            'coh_manage_settings',
            'coh-settings',
            array( $this, 'render_settings' )
        );
    }

    /**
     * Enqueue CSS and JS on plugin pages only.
     */
    public function enqueue_assets( string $hook ): void {
        $pages = array(
            'toplevel_page_coh-dashboard',
            'operations-hub_page_coh-clients',
            'operations-hub_page_coh-api-vault',
            'operations-hub_page_coh-settings',
        );

        // Also match translated/sanitized slugs.
        $is_coh_page = false;
        foreach ( $pages as $p ) {
            if ( strpos( $hook, 'coh-' ) !== false ) {
                $is_coh_page = true;
                break;
            }
        }

        if ( ! $is_coh_page ) {
            return;
        }

        wp_enqueue_style(
            'coh-admin-style',
            COH_PLUGIN_URL . 'admin/css/admin-style.css',
            array(),
            COH_VERSION
        );

        wp_enqueue_script(
            'coh-admin-script',
            COH_PLUGIN_URL . 'admin/js/admin-script.js',
            array( 'jquery' ),
            COH_VERSION,
            true
        );

        wp_localize_script( 'coh-admin-script', 'cohAdmin', array(
            'restUrl'  => rest_url( 'coh/v1/' ),
            'nonce'    => wp_create_nonce( 'wp_rest' ),
            'adminUrl' => admin_url( 'admin.php' ),
        ) );
    }

    // =========================================================================
    // Page renderers — load view files.
    // =========================================================================

    public function render_dashboard(): void {
        require_once COH_PLUGIN_DIR . 'admin/views/dashboard.php';
    }

    public function render_clients(): void {
        require_once COH_PLUGIN_DIR . 'admin/views/clients.php';
    }

    public function render_api_vault(): void {
        require_once COH_PLUGIN_DIR . 'admin/views/api-vault.php';
    }

    public function render_settings(): void {
        require_once COH_PLUGIN_DIR . 'admin/views/settings.php';
    }
}
