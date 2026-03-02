<?php
/**
 * Plugin deactivation.
 *
 * @package ClientOperationsHub
 */

namespace COH;

defined( 'ABSPATH' ) || exit;

class Deactivator {

    /**
     * Run on deactivation.
     */
    public static function deactivate() {
        wp_clear_scheduled_hook( 'coh_process_reminders' );
        wp_clear_scheduled_hook( 'coh_daily_overdue_check' );
        flush_rewrite_rules();
    }
}
