<?php
/**
 * Admin view: API Key Vault.
 *
 * @package ClientOperationsHub
 */

use COH\Modules\Api_Vault;

defined( 'ABSPATH' ) || exit;

$stored_keys = Api_Vault::get_all();
$services    = Api_Vault::get_supported_services();
$audit_log   = Api_Vault::get_audit_log( 20 );

// Index stored keys by service_name.
$stored_index = array();
foreach ( $stored_keys as $key ) {
    $stored_index[ $key['service_name'] ] = $key;
}
?>
<div class="wrap coh-wrap">
    <h1>API-Schluessel Verwaltung</h1>
    <p>Alle API-Keys werden AES-256 verschluesselt in der Datenbank gespeichert.</p>

    <div class="coh-dashboard-columns">
        <div class="coh-dashboard-main">

            <div class="coh-card">
                <h2>Services</h2>
                <table class="coh-table">
                    <thead>
                        <tr>
                            <th>Service</th>
                            <th>Status</th>
                            <th>Letzter Test</th>
                            <th>API-Key</th>
                            <th>Aktionen</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ( $services as $name => $service ) :
                            $stored = $stored_index[ $name ] ?? null;
                            $status = $stored['status'] ?? 'not_configured';
                        ?>
                        <tr id="coh-service-<?php echo esc_attr( $name ); ?>">
                            <td><strong><?php echo esc_html( $service['label'] ); ?></strong></td>
                            <td>
                                <span class="coh-api-status coh-api-status--<?php echo esc_attr( $status ); ?>">
                                    <?php
                                    $status_labels = array(
                                        'connected'      => 'Verbunden',
                                        'error'          => 'Fehler',
                                        'untested'       => 'Nicht getestet',
                                        'not_configured' => 'Nicht konfiguriert',
                                    );
                                    echo esc_html( $status_labels[ $status ] ?? $status );
                                    ?>
                                </span>
                            </td>
                            <td>
                                <?php echo $stored && $stored['last_tested']
                                    ? esc_html( gmdate( 'd.m.Y H:i', strtotime( $stored['last_tested'] ) ) )
                                    : '-'; ?>
                            </td>
                            <td>
                                <div class="coh-api-key-input">
                                    <input type="password"
                                           class="regular-text coh-api-key-field"
                                           data-service="<?php echo esc_attr( $name ); ?>"
                                           placeholder="<?php echo $stored ? 'Key gespeichert (zum Aendern neuen eingeben)' : 'API Key eingeben...'; ?>"
                                           autocomplete="off">
                                    <?php if ( 'activecampaign' === $name ) : ?>
                                    <input type="url"
                                           class="regular-text coh-api-extra-field"
                                           data-service="<?php echo esc_attr( $name ); ?>"
                                           data-field="base_url"
                                           placeholder="https://your-account.api-us1.com"
                                           autocomplete="off">
                                    <?php endif; ?>
                                </div>
                            </td>
                            <td>
                                <button class="button button-primary coh-save-api-key" data-service="<?php echo esc_attr( $name ); ?>">Speichern</button>
                                <button class="button coh-test-api-key" data-service="<?php echo esc_attr( $name ); ?>" <?php echo $stored ? '' : 'disabled'; ?>>Testen</button>
                                <?php if ( $stored ) : ?>
                                <button class="button coh-delete-api-key" data-service="<?php echo esc_attr( $name ); ?>">Loeschen</button>
                                <?php endif; ?>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="coh-dashboard-sidebar">
            <div class="coh-card">
                <h2>Audit Log</h2>
                <div class="coh-timeline">
                    <?php foreach ( $audit_log as $entry ) : ?>
                    <div class="coh-timeline-entry">
                        <span class="coh-timeline-date"><?php echo esc_html( gmdate( 'd.m.Y H:i', strtotime( $entry['created_at'] ) ) ); ?></span>
                        <strong><?php echo esc_html( $entry['service_label'] ?: $entry['service_name'] ); ?></strong>
                        <span class="coh-audit-action coh-audit-action--<?php echo esc_attr( $entry['action'] ); ?>">
                            <?php echo esc_html( $entry['action'] ); ?>
                        </span>
                        <?php if ( ! empty( $entry['display_name'] ) ) : ?>
                        <span class="coh-timeline-user">von <?php echo esc_html( $entry['display_name'] ); ?></span>
                        <?php endif; ?>
                    </div>
                    <?php endforeach; ?>
                    <?php if ( empty( $audit_log ) ) : ?>
                    <p class="coh-empty">Noch keine Eintraege.</p>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>
</div>
