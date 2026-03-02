<?php
/**
 * Task Templates manager.
 *
 * @package ClientOperationsHub
 */

namespace COH;

defined( 'ABSPATH' ) || exit;

class Task_Templates {

    /**
     * Get all active templates, optionally filtered by conditions.
     *
     * @param array $context Client context for conditional filtering (package_type, monthly_volume, tier, industry).
     * @return array
     */
    public static function get_templates( array $context = array() ): array {
        global $wpdb;

        $table     = $wpdb->prefix . 'coh_task_templates';
        $templates = $wpdb->get_results(
            "SELECT * FROM {$table} WHERE is_active = 1 ORDER BY day_offset ASC, sort_order ASC",
            ARRAY_A
        );

        if ( empty( $context ) ) {
            return $templates;
        }

        // Filter templates by conditions.
        return array_filter( $templates, function ( $tpl ) use ( $context ) {
            if ( empty( $tpl['conditions'] ) ) {
                return true;
            }

            $conditions = json_decode( $tpl['conditions'], true );
            if ( ! is_array( $conditions ) ) {
                return true;
            }

            foreach ( $conditions as $field => $rule ) {
                $value = $context[ $field ] ?? null;
                if ( null === $value ) {
                    continue;
                }

                if ( is_array( $rule ) ) {
                    // Operator-based: {"monthly_volume": {">=": 5000}}
                    foreach ( $rule as $op => $threshold ) {
                        switch ( $op ) {
                            case '>=':
                                if ( (float) $value < (float) $threshold ) return false;
                                break;
                            case '<=':
                                if ( (float) $value > (float) $threshold ) return false;
                                break;
                            case '>':
                                if ( (float) $value <= (float) $threshold ) return false;
                                break;
                            case '<':
                                if ( (float) $value >= (float) $threshold ) return false;
                                break;
                            case '=':
                            case '==':
                                if ( $value != $threshold ) return false;
                                break;
                            case '!=':
                                if ( $value == $threshold ) return false;
                                break;
                            case 'in':
                                if ( ! in_array( $value, (array) $threshold, false ) ) return false;
                                break;
                        }
                    }
                } else {
                    // Simple equality: {"package_type": "SEO"}
                    if ( $value !== $rule ) {
                        return false;
                    }
                }
            }

            return true;
        } );
    }

    /**
     * Get a single template by ID.
     */
    public static function get( int $id ): ?array {
        global $wpdb;
        $table  = $wpdb->prefix . 'coh_task_templates';
        $result = $wpdb->get_row( $wpdb->prepare( "SELECT * FROM {$table} WHERE id = %d", $id ), ARRAY_A );
        return $result ?: null;
    }

    /**
     * Update a template.
     */
    public static function update( int $id, array $data ): bool {
        global $wpdb;
        $table  = $wpdb->prefix . 'coh_task_templates';
        $result = $wpdb->update( $table, $data, array( 'id' => $id ) );
        return $result !== false;
    }

    /**
     * Create a new template.
     */
    public static function create( array $data ): int {
        global $wpdb;
        $table = $wpdb->prefix . 'coh_task_templates';
        $wpdb->insert( $table, $data );
        return (int) $wpdb->insert_id;
    }

    /**
     * Delete (soft) a template.
     */
    public static function deactivate( int $id ): bool {
        return self::update( $id, array( 'is_active' => 0 ) );
    }
}
