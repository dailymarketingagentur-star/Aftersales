<?php
/**
 * Admin view: Clients list and detail.
 *
 * @package ClientOperationsHub
 */

use COH\Modules\Client_Intake;
use COH\Modules\Task_Engine;

defined( 'ABSPATH' ) || exit;

$client_id = isset( $_GET['client_id'] ) ? (int) $_GET['client_id'] : 0; // phpcs:ignore WordPress.Security.NonceVerification
$action    = isset( $_GET['action'] ) ? sanitize_text_field( wp_unslash( $_GET['action'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification

// --- Single Client Detail View ---
if ( $client_id > 0 ) :
    $client    = Client_Intake::get( $client_id );
    if ( ! $client ) {
        echo '<div class="wrap"><div class="notice notice-error"><p>Kunde nicht gefunden.</p></div></div>';
        return;
    }
    $tasks     = Task_Engine::get_tasks( $client_id );
    $phase     = Task_Engine::get_current_phase( $client_id );
    $next_task = Task_Engine::get_next_task( $client_id );
    $activity  = Client_Intake::get_activity_log( $client_id );
    $today     = current_time( 'Y-m-d' );
?>
<div class="wrap coh-wrap">
    <h1>
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=coh-clients' ) ); ?>">&larr; Alle Kunden</a>
        &nbsp;|&nbsp; <?php echo esc_html( $client['company_name'] ); ?>
        <span class="coh-tier-badge coh-tier--<?php echo esc_attr( $client['tier'] ); ?>"><?php echo esc_html( ucfirst( $client['tier'] ) ); ?></span>
    </h1>

    <div class="coh-dashboard-columns">
        <div class="coh-dashboard-main">

            <!-- Client Info Card -->
            <div class="coh-card">
                <h2>Kundendaten</h2>
                <div class="coh-detail-grid">
                    <div><strong>Kontakt:</strong> <?php echo esc_html( $client['contact_name'] ); ?></div>
                    <div><strong>Email:</strong> <a href="mailto:<?php echo esc_attr( $client['email'] ); ?>"><?php echo esc_html( $client['email'] ); ?></a></div>
                    <div><strong>Telefon:</strong> <?php echo esc_html( $client['phone'] ); ?></div>
                    <div><strong>Website:</strong> <?php echo $client['website'] ? '<a href="' . esc_url( $client['website'] ) . '" target="_blank">' . esc_html( $client['website'] ) . '</a>' : '-'; ?></div>
                    <div><strong>Paket:</strong> <?php echo esc_html( $client['package_type'] ); ?></div>
                    <div><strong>Branche:</strong> <?php echo esc_html( $client['industry'] ); ?></div>
                    <div><strong>Volumen:</strong> <?php echo esc_html( number_format( (float) $client['monthly_volume'], 0, ',', '.' ) ); ?> EUR/Monat</div>
                    <div><strong>Startdatum:</strong> <?php echo esc_html( gmdate( 'd.m.Y', strtotime( $client['start_date'] ) ) ); ?></div>
                    <div><strong>Phase:</strong> <?php echo esc_html( $phase ); ?> von 11</div>
                    <div>
                        <strong>Health Score:</strong>
                        <span class="coh-health-score" data-score="<?php echo esc_attr( $client['health_score'] ); ?>">
                            <?php echo esc_html( $client['health_score'] ); ?>/100
                        </span>
                        <input type="range" min="0" max="100" value="<?php echo esc_attr( $client['health_score'] ); ?>"
                               class="coh-health-slider" data-client-id="<?php echo esc_attr( $client_id ); ?>">
                    </div>
                </div>
                <?php if ( ! empty( $client['address'] ) ) : ?>
                <div style="margin-top:10px"><strong>Adresse:</strong><br><?php echo nl2br( esc_html( $client['address'] ) ); ?></div>
                <?php endif; ?>
                <?php if ( ! empty( $client['notes'] ) ) : ?>
                <div style="margin-top:10px"><strong>Notizen:</strong><br><?php echo nl2br( esc_html( $client['notes'] ) ); ?></div>
                <?php endif; ?>
            </div>

            <!-- Tasks -->
            <div class="coh-card">
                <h2>Aufgaben (<?php echo count( $tasks ); ?>)</h2>
                <div class="coh-task-filters">
                    <button class="button coh-task-filter active" data-filter="all">Alle</button>
                    <button class="button coh-task-filter" data-filter="pending">Offen</button>
                    <button class="button coh-task-filter" data-filter="completed">Erledigt</button>
                    <button class="button coh-task-filter" data-filter="skipped">Uebersprungen</button>
                </div>
                <table class="coh-table coh-task-table">
                    <thead>
                        <tr>
                            <th>Phase</th>
                            <th>Aufgabe</th>
                            <th>Typ</th>
                            <th>Faellig</th>
                            <th>Status</th>
                            <th>Aktion</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ( $tasks as $task ) :
                            $is_overdue = ( in_array( $task['status'], array( 'pending', 'in_progress' ), true ) && $task['due_date'] < $today );
                            $row_class  = $is_overdue ? 'coh-row-overdue' : '';
                            $row_class .= ' coh-task-status-' . $task['status'];
                        ?>
                        <tr class="<?php echo esc_attr( $row_class ); ?>" data-status="<?php echo esc_attr( $task['status'] ); ?>">
                            <td><span class="coh-phase-badge">P<?php echo esc_html( $task['phase'] ); ?></span></td>
                            <td>
                                <strong><?php echo esc_html( $task['title'] ); ?></strong>
                                <span class="coh-badge coh-badge--<?php echo esc_attr( $task['priority'] ); ?>"><?php echo esc_html( ucfirst( $task['priority'] ) ); ?></span>
                                <?php if ( ! empty( $task['description'] ) ) : ?>
                                <p class="coh-task-desc"><?php echo esc_html( $task['description'] ); ?></p>
                                <?php endif; ?>
                                <?php if ( ! empty( $task['notes'] ) ) : ?>
                                <p class="coh-task-notes"><em><?php echo esc_html( $task['notes'] ); ?></em></p>
                                <?php endif; ?>
                            </td>
                            <td><span class="coh-type-badge"><?php echo esc_html( $task['task_type'] ); ?></span></td>
                            <td>
                                <?php echo esc_html( gmdate( 'd.m.Y', strtotime( $task['due_date'] ) ) ); ?>
                                <?php if ( $is_overdue ) : ?>
                                    <span class="coh-overdue-days">+<?php echo (int) ( ( strtotime( $today ) - strtotime( $task['due_date'] ) ) / 86400 ); ?>d</span>
                                <?php endif; ?>
                            </td>
                            <td><span class="coh-status-badge coh-status--<?php echo esc_attr( $task['status'] ); ?>"><?php echo esc_html( ucfirst( $task['status'] ) ); ?></span></td>
                            <td>
                                <?php if ( in_array( $task['status'], array( 'pending', 'in_progress' ), true ) ) : ?>
                                <button class="button button-primary button-small coh-complete-task" data-task-id="<?php echo esc_attr( $task['id'] ); ?>">Erledigt</button>
                                <button class="button button-small coh-skip-task" data-task-id="<?php echo esc_attr( $task['id'] ); ?>">Skip</button>
                                <?php elseif ( 'completed' === $task['status'] && $task['completed_at'] ) : ?>
                                    <small><?php echo esc_html( gmdate( 'd.m. H:i', strtotime( $task['completed_at'] ) ) ); ?></small>
                                <?php endif; ?>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Sidebar: Timeline -->
        <div class="coh-dashboard-sidebar">
            <div class="coh-card">
                <h2>Aktivitaeten</h2>
                <!-- Add Note -->
                <div class="coh-add-note">
                    <textarea id="coh-note-text" placeholder="Notiz hinzufuegen..." rows="2" class="large-text"></textarea>
                    <button class="button coh-add-note-btn" data-client-id="<?php echo esc_attr( $client_id ); ?>">Notiz speichern</button>
                </div>
                <div class="coh-timeline">
                    <?php foreach ( $activity as $entry ) : ?>
                    <div class="coh-timeline-entry coh-activity-type--<?php echo esc_attr( $entry['activity_type'] ); ?>">
                        <span class="coh-timeline-date"><?php echo esc_html( gmdate( 'd.m.Y H:i', strtotime( $entry['created_at'] ) ) ); ?></span>
                        <strong><?php echo esc_html( $entry['title'] ); ?></strong>
                        <?php if ( ! empty( $entry['description'] ) ) : ?>
                        <p><?php echo esc_html( $entry['description'] ); ?></p>
                        <?php endif; ?>
                        <?php if ( ! empty( $entry['display_name'] ) ) : ?>
                        <span class="coh-timeline-user"><?php echo esc_html( $entry['display_name'] ); ?></span>
                        <?php endif; ?>
                    </div>
                    <?php endforeach; ?>
                    <?php if ( empty( $activity ) ) : ?>
                    <p class="coh-empty">Noch keine Aktivitaeten.</p>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>
</div>

<?php
    return;
endif;

// --- New Client Form ---
if ( 'new' === $action ) :
?>
<div class="wrap coh-wrap">
    <h1>
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=coh-clients' ) ); ?>">&larr; Alle Kunden</a>
        &nbsp;|&nbsp; Neuen Kunden anlegen
    </h1>

    <div class="coh-card" style="max-width:700px">
        <form id="coh-new-client-form" class="coh-form">
            <div class="coh-form-row">
                <label>Firmenname *</label>
                <input type="text" name="company_name" required class="regular-text">
            </div>
            <div class="coh-form-row">
                <label>Kontaktperson *</label>
                <input type="text" name="contact_name" required class="regular-text">
            </div>
            <div class="coh-form-row">
                <label>Email *</label>
                <input type="email" name="email" required class="regular-text">
            </div>
            <div class="coh-form-row">
                <label>Telefon</label>
                <input type="text" name="phone" class="regular-text">
            </div>
            <div class="coh-form-row">
                <label>Website</label>
                <input type="url" name="website" class="regular-text">
            </div>
            <div class="coh-form-row">
                <label>Adresse</label>
                <textarea name="address" rows="3" class="large-text"></textarea>
            </div>
            <div class="coh-form-row">
                <label>Paket</label>
                <select name="package_type">
                    <option value="">-- Waehlen --</option>
                    <option value="Website">Website</option>
                    <option value="SEO">SEO</option>
                    <option value="Content">Content Marketing</option>
                    <option value="PPC">PPC / Ads</option>
                    <option value="Social Media">Social Media</option>
                    <option value="Email Marketing">Email Marketing</option>
                    <option value="Full-Service">Full-Service</option>
                </select>
            </div>
            <div class="coh-form-row">
                <label>Branche</label>
                <input type="text" name="industry" class="regular-text">
            </div>
            <div class="coh-form-row">
                <label>Monatliches Volumen (EUR)</label>
                <input type="number" name="monthly_volume" min="0" step="100" class="regular-text">
            </div>
            <div class="coh-form-row">
                <label>Startdatum *</label>
                <input type="date" name="start_date" required value="<?php echo esc_attr( current_time( 'Y-m-d' ) ); ?>">
            </div>
            <div class="coh-form-row">
                <label>Notizen</label>
                <textarea name="notes" rows="3" class="large-text"></textarea>
            </div>
            <div class="coh-form-actions">
                <button type="submit" class="button button-primary button-hero">Kunden anlegen &amp; Pipeline starten</button>
            </div>
        </form>
    </div>
</div>

<?php
    return;
endif;

// --- Client List ---
$clients = Client_Intake::get_all( array( 'status' => 'active' ) );
$today   = current_time( 'Y-m-d' );
?>
<div class="wrap coh-wrap">
    <h1>
        Kunden
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=coh-clients&action=new' ) ); ?>" class="page-title-action">Neuer Kunde</a>
    </h1>

    <div class="coh-card">
        <div class="coh-list-toolbar">
            <input type="search" id="coh-client-search" placeholder="Suchen..." class="regular-text">
        </div>
        <table class="coh-table coh-client-table">
            <thead>
                <tr>
                    <th>Ampel</th>
                    <th>Firma</th>
                    <th>Kontakt</th>
                    <th>Paket</th>
                    <th>Tier</th>
                    <th>Health</th>
                    <th>Phase</th>
                    <th>Naechste Aufgabe</th>
                    <th>Start</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ( $clients as $client ) :
                    $cid       = (int) $client['id'];
                    $next_task = Task_Engine::get_next_task( $cid );
                    $phase     = Task_Engine::get_current_phase( $cid );

                    // Calculate signal.
                    $signal = 'green';
                    if ( (int) $client['health_score'] < 30 || ( $next_task && $next_task['due_date'] < $today ) ) {
                        $signal = 'red';
                    } elseif ( (int) $client['health_score'] < 50 || ( $next_task && ( strtotime( $next_task['due_date'] ) - strtotime( $today ) ) / 86400 <= 2 ) ) {
                        $signal = 'yellow';
                    }
                ?>
                <tr>
                    <td><span class="coh-signal-dot coh-signal--<?php echo esc_attr( $signal ); ?>"></span></td>
                    <td>
                        <a href="<?php echo esc_url( admin_url( 'admin.php?page=coh-clients&client_id=' . $cid ) ); ?>">
                            <strong><?php echo esc_html( $client['company_name'] ); ?></strong>
                        </a>
                    </td>
                    <td><?php echo esc_html( $client['contact_name'] ); ?></td>
                    <td><?php echo esc_html( $client['package_type'] ); ?></td>
                    <td><span class="coh-tier-badge coh-tier--<?php echo esc_attr( $client['tier'] ); ?>"><?php echo esc_html( ucfirst( $client['tier'] ) ); ?></span></td>
                    <td><span class="coh-health-score" data-score="<?php echo esc_attr( $client['health_score'] ); ?>"><?php echo esc_html( $client['health_score'] ); ?></span></td>
                    <td>Phase <?php echo esc_html( $phase ); ?></td>
                    <td>
                        <?php if ( $next_task ) : ?>
                            <?php echo esc_html( $next_task['title'] ); ?>
                            <small>(<?php echo esc_html( gmdate( 'd.m.', strtotime( $next_task['due_date'] ) ) ); ?>)</small>
                        <?php else : ?>
                            <span class="coh-empty">-</span>
                        <?php endif; ?>
                    </td>
                    <td><?php echo esc_html( gmdate( 'd.m.Y', strtotime( $client['start_date'] ) ) ); ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
        <?php if ( empty( $clients ) ) : ?>
        <p class="coh-empty" style="padding:20px;text-align:center">
            Noch keine Kunden. <a href="<?php echo esc_url( admin_url( 'admin.php?page=coh-clients&action=new' ) ); ?>">Ersten Kunden anlegen</a>
        </p>
        <?php endif; ?>
    </div>
</div>
