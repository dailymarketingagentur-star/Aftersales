<?php
/**
 * Admin view: Operations Dashboard.
 *
 * @package ClientOperationsHub
 */

use COH\Modules\Dashboard;
use COH\Modules\Task_Engine;

defined( 'ABSPATH' ) || exit;

$data          = Dashboard::get_dashboard_data();
$task_stats    = $data['task_stats'];
$client_stats  = $data['client_stats'];
$overdue       = $data['overdue_tasks'];
$today_tasks   = $data['tasks_today'];
$week_tasks    = $data['tasks_week'];
$clients       = $data['clients'];
?>
<div class="wrap coh-wrap">
    <h1>Operations Dashboard</h1>

    <!-- KPI Cards -->
    <div class="coh-kpi-grid">
        <div class="coh-kpi-card">
            <span class="coh-kpi-number"><?php echo esc_html( $client_stats['active'] ); ?></span>
            <span class="coh-kpi-label">Aktive Kunden</span>
        </div>
        <div class="coh-kpi-card">
            <span class="coh-kpi-number"><?php echo esc_html( $task_stats['due_today'] ); ?></span>
            <span class="coh-kpi-label">Aufgaben heute</span>
        </div>
        <div class="coh-kpi-card coh-kpi-card--danger">
            <span class="coh-kpi-number"><?php echo esc_html( $task_stats['overdue'] ); ?></span>
            <span class="coh-kpi-label">Ueberfaellig</span>
        </div>
        <div class="coh-kpi-card">
            <span class="coh-kpi-number"><?php echo esc_html( $task_stats['completion_rate'] ); ?>%</span>
            <span class="coh-kpi-label">Completion Rate</span>
        </div>
        <div class="coh-kpi-card">
            <span class="coh-kpi-number"><?php echo esc_html( $client_stats['avg_health'] ); ?></span>
            <span class="coh-kpi-label">Avg Health Score</span>
        </div>
    </div>

    <div class="coh-dashboard-columns">
        <!-- Left: Tasks -->
        <div class="coh-dashboard-main">

            <!-- Overdue -->
            <?php if ( ! empty( $overdue ) ) : ?>
            <div class="coh-card coh-card--danger">
                <h2>Ueberfaellige Aufgaben (<?php echo count( $overdue ); ?>)</h2>
                <table class="coh-table">
                    <thead>
                        <tr>
                            <th>Kunde</th>
                            <th>Aufgabe</th>
                            <th>Faellig</th>
                            <th>Tage</th>
                            <th>Aktion</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ( $overdue as $task ) :
                            $days = (int) ( ( strtotime( current_time( 'Y-m-d' ) ) - strtotime( $task['due_date'] ) ) / 86400 );
                        ?>
                        <tr>
                            <td>
                                <a href="<?php echo esc_url( admin_url( 'admin.php?page=coh-clients&client_id=' . $task['client_id'] ) ); ?>">
                                    <?php echo esc_html( $task['company_name'] ); ?>
                                </a>
                            </td>
                            <td>
                                <strong><?php echo esc_html( $task['title'] ); ?></strong>
                                <span class="coh-badge coh-badge--<?php echo esc_attr( $task['priority'] ); ?>"><?php echo esc_html( ucfirst( $task['priority'] ) ); ?></span>
                            </td>
                            <td><?php echo esc_html( gmdate( 'd.m.Y', strtotime( $task['due_date'] ) ) ); ?></td>
                            <td><span class="coh-overdue-days">+<?php echo esc_html( $days ); ?>d</span></td>
                            <td>
                                <button class="button coh-complete-task" data-task-id="<?php echo esc_attr( $task['id'] ); ?>">Erledigt</button>
                                <button class="button coh-skip-task" data-task-id="<?php echo esc_attr( $task['id'] ); ?>">Ueberspringen</button>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            <?php endif; ?>

            <!-- Today -->
            <div class="coh-card">
                <h2>Heute faellig (<?php echo count( $today_tasks ); ?>)</h2>
                <?php if ( empty( $today_tasks ) ) : ?>
                    <p class="coh-empty">Keine Aufgaben fuer heute. Alles erledigt!</p>
                <?php else : ?>
                <table class="coh-table">
                    <thead>
                        <tr>
                            <th>Kunde</th>
                            <th>Aufgabe</th>
                            <th>Typ</th>
                            <th>Prioritaet</th>
                            <th>Aktion</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ( $today_tasks as $task ) : ?>
                        <tr>
                            <td>
                                <a href="<?php echo esc_url( admin_url( 'admin.php?page=coh-clients&client_id=' . $task['client_id'] ) ); ?>">
                                    <?php echo esc_html( $task['company_name'] ); ?>
                                </a>
                                <span class="coh-tier-badge coh-tier--<?php echo esc_attr( $task['tier'] ); ?>"><?php echo esc_html( ucfirst( $task['tier'] ) ); ?></span>
                            </td>
                            <td><strong><?php echo esc_html( $task['title'] ); ?></strong></td>
                            <td><span class="coh-type-badge"><?php echo esc_html( $task['task_type'] ); ?></span></td>
                            <td><span class="coh-badge coh-badge--<?php echo esc_attr( $task['priority'] ); ?>"><?php echo esc_html( ucfirst( $task['priority'] ) ); ?></span></td>
                            <td>
                                <button class="button button-primary coh-complete-task" data-task-id="<?php echo esc_attr( $task['id'] ); ?>">Erledigt</button>
                                <button class="button coh-skip-task" data-task-id="<?php echo esc_attr( $task['id'] ); ?>">Ueberspringen</button>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
                <?php endif; ?>
            </div>

            <!-- This Week -->
            <div class="coh-card">
                <h2>Diese Woche (<?php echo count( $week_tasks ); ?>)</h2>
                <?php if ( empty( $week_tasks ) ) : ?>
                    <p class="coh-empty">Keine weiteren Aufgaben diese Woche.</p>
                <?php else : ?>
                <table class="coh-table">
                    <thead>
                        <tr>
                            <th>Datum</th>
                            <th>Kunde</th>
                            <th>Aufgabe</th>
                            <th>Prioritaet</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ( $week_tasks as $task ) : ?>
                        <tr>
                            <td><?php echo esc_html( gmdate( 'D d.m.', strtotime( $task['due_date'] ) ) ); ?></td>
                            <td>
                                <a href="<?php echo esc_url( admin_url( 'admin.php?page=coh-clients&client_id=' . $task['client_id'] ) ); ?>">
                                    <?php echo esc_html( $task['company_name'] ); ?>
                                </a>
                            </td>
                            <td><?php echo esc_html( $task['title'] ); ?></td>
                            <td><span class="coh-badge coh-badge--<?php echo esc_attr( $task['priority'] ); ?>"><?php echo esc_html( ucfirst( $task['priority'] ) ); ?></span></td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
                <?php endif; ?>
            </div>
        </div>

        <!-- Right: Client Overview -->
        <div class="coh-dashboard-sidebar">
            <div class="coh-card">
                <h2>Kunden-Uebersicht</h2>
                <div class="coh-client-list">
                    <?php foreach ( $clients as $client ) : ?>
                    <a href="<?php echo esc_url( admin_url( 'admin.php?page=coh-clients&client_id=' . $client['id'] ) ); ?>" class="coh-client-row coh-signal--<?php echo esc_attr( $client['signal'] ); ?>">
                        <span class="coh-signal-dot"></span>
                        <div class="coh-client-info">
                            <strong><?php echo esc_html( $client['company_name'] ); ?></strong>
                            <span class="coh-client-meta">
                                Phase <?php echo esc_html( $client['phase'] ); ?> |
                                Health: <?php echo esc_html( $client['health_score'] ); ?> |
                                <?php echo esc_html( ucfirst( $client['tier'] ) ); ?>
                            </span>
                            <?php if ( $client['next_task'] ) : ?>
                            <span class="coh-client-next-task">
                                Naechste: <?php echo esc_html( $client['next_task']['title'] ); ?>
                                (<?php echo esc_html( gmdate( 'd.m.', strtotime( $client['next_task']['due_date'] ) ) ); ?>)
                            </span>
                            <?php endif; ?>
                        </div>
                    </a>
                    <?php endforeach; ?>

                    <?php if ( empty( $clients ) ) : ?>
                        <p class="coh-empty">Noch keine Kunden angelegt.</p>
                        <a href="<?php echo esc_url( admin_url( 'admin.php?page=coh-clients&action=new' ) ); ?>" class="button button-primary">Ersten Kunden anlegen</a>
                    <?php endif; ?>
                </div>
            </div>

            <!-- Tier Distribution -->
            <div class="coh-card">
                <h2>Tier-Verteilung</h2>
                <?php
                $tiers = $client_stats['tiers'];
                $tier_colors = array( 'bronze' => '#cd7f32', 'silber' => '#c0c0c0', 'gold' => '#ffd700', 'platin' => '#e5e4e2' );
                foreach ( $tier_colors as $tier => $color ) :
                    $count = $tiers[ $tier ] ?? 0;
                ?>
                <div class="coh-tier-row">
                    <span class="coh-tier-dot" style="background:<?php echo esc_attr( $color ); ?>"></span>
                    <span class="coh-tier-name"><?php echo esc_html( ucfirst( $tier ) ); ?></span>
                    <span class="coh-tier-count"><?php echo esc_html( $count ); ?></span>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
    </div>
</div>
