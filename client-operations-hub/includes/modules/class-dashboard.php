<?php
/**
 * Module B4: Operations Dashboard
 *
 * Aggregated views for daily operations.
 *
 * @package ClientOperationsHub
 */

namespace COH\Modules;

defined( 'ABSPATH' ) || exit;

class Dashboard {

    /**
     * Get full dashboard data.
     */
    public static function get_dashboard_data(): array {
        return array(
            'task_stats'     => Task_Engine::get_stats(),
            'overdue_tasks'  => Task_Engine::get_overdue_tasks(),
            'tasks_today'    => Task_Engine::get_tasks_due_today(),
            'tasks_week'     => Task_Engine::get_tasks_upcoming_week(),
            'clients'        => self::get_clients_overview(),
            'client_stats'   => self::get_client_stats(),
        );
    }

    /**
     * Get all active clients with their current status.
     */
    public static function get_clients_overview(): array {
        $clients = Client_Intake::get_all( array( 'status' => 'active' ) );
        $today   = current_time( 'Y-m-d' );

        foreach ( $clients as &$client ) {
            $cid             = (int) $client['id'];
            $next_task       = Task_Engine::get_next_task( $cid );
            $client['phase'] = Task_Engine::get_current_phase( $cid );

            $client['next_task']      = $next_task;
            $client['next_task_date'] = $next_task['due_date'] ?? null;

            // Traffic light: green / yellow / red.
            $client['signal'] = self::calculate_signal( $client, $next_task, $today );
        }
        unset( $client );

        return $clients;
    }

    /**
     * Calculate traffic-light signal for a client.
     */
    private static function calculate_signal( array $client, ?array $next_task, string $today ): string {
        // Red: overdue tasks or very low health score.
        if ( (int) $client['health_score'] < 30 ) {
            return 'red';
        }

        if ( $next_task && $next_task['due_date'] < $today ) {
            return 'red';
        }

        // Yellow: task due within 2 days or health score mediocre.
        if ( (int) $client['health_score'] < 50 ) {
            return 'yellow';
        }

        if ( $next_task ) {
            $days_until = ( strtotime( $next_task['due_date'] ) - strtotime( $today ) ) / 86400;
            if ( $days_until <= 2 ) {
                return 'yellow';
            }
        }

        return 'green';
    }

    /**
     * Get aggregated client statistics.
     */
    public static function get_client_stats(): array {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_clients';

        $total  = (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$table}" );
        $active = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$table} WHERE status = %s", 'active' ) );

        $avg_health = (float) $wpdb->get_var( $wpdb->prepare(
            "SELECT AVG(health_score) FROM {$table} WHERE status = %s",
            'active'
        ) );

        $tiers = $wpdb->get_results( $wpdb->prepare(
            "SELECT tier, COUNT(*) as count FROM {$table} WHERE status = %s GROUP BY tier",
            'active'
        ), ARRAY_A ) ?: array();

        $tier_counts = array();
        foreach ( $tiers as $t ) {
            $tier_counts[ $t['tier'] ] = (int) $t['count'];
        }

        return array(
            'total'         => $total,
            'active'        => $active,
            'avg_health'    => round( $avg_health, 1 ),
            'tiers'         => $tier_counts,
        );
    }
}
