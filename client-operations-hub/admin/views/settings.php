<?php
/**
 * Admin view: Plugin Settings.
 *
 * @package ClientOperationsHub
 */

defined( 'ABSPATH' ) || exit;

// Handle save.
if ( isset( $_POST['coh_save_settings'] ) && check_admin_referer( 'coh_settings_nonce' ) ) {
    $settings = array(
        'reminder_email'         => sanitize_email( wp_unslash( $_POST['reminder_email'] ?? '' ) ),
        'escalation_email'       => sanitize_email( wp_unslash( $_POST['escalation_email'] ?? '' ) ),
        'slack_channel'          => sanitize_text_field( wp_unslash( $_POST['slack_channel'] ?? '' ) ),
        'slack_reminder_channel' => sanitize_text_field( wp_unslash( $_POST['slack_reminder_channel'] ?? '' ) ),
        'clickup_list_id'        => sanitize_text_field( wp_unslash( $_POST['clickup_list_id'] ?? '' ) ),
        'webhook_secret'         => sanitize_text_field( wp_unslash( $_POST['webhook_secret'] ?? '' ) ),
    );
    update_option( 'coh_settings', $settings );
    echo '<div class="notice notice-success is-dismissible"><p>Einstellungen gespeichert.</p></div>';
}

$settings = get_option( 'coh_settings', array() );
$webhook_url = rest_url( 'coh/v1/webhook/new-client' );
?>
<div class="wrap coh-wrap">
    <h1>Einstellungen</h1>

    <form method="post" class="coh-form">
        <?php wp_nonce_field( 'coh_settings_nonce' ); ?>

        <div class="coh-card" style="max-width:700px">
            <h2>Benachrichtigungen</h2>

            <div class="coh-form-row">
                <label>Reminder-Email</label>
                <input type="email" name="reminder_email" class="regular-text"
                       value="<?php echo esc_attr( $settings['reminder_email'] ?? '' ); ?>"
                       placeholder="<?php echo esc_attr( get_option( 'admin_email' ) ); ?>">
                <p class="description">Taegliche Aufgaben-Erinnerungen. Standard: Admin-Email.</p>
            </div>

            <div class="coh-form-row">
                <label>Eskalations-Email</label>
                <input type="email" name="escalation_email" class="regular-text"
                       value="<?php echo esc_attr( $settings['escalation_email'] ?? '' ); ?>"
                       placeholder="<?php echo esc_attr( get_option( 'admin_email' ) ); ?>">
                <p class="description">Fuer ueberfaellige Aufgaben und Churn-Warnungen.</p>
            </div>
        </div>

        <div class="coh-card" style="max-width:700px">
            <h2>Slack</h2>

            <div class="coh-form-row">
                <label>Neukunden-Channel</label>
                <input type="text" name="slack_channel" class="regular-text"
                       value="<?php echo esc_attr( $settings['slack_channel'] ?? '' ); ?>"
                       placeholder="#neukunden">
                <p class="description">Slack-Channel fuer Neukunden-Benachrichtigungen.</p>
            </div>

            <div class="coh-form-row">
                <label>Reminder-Channel</label>
                <input type="text" name="slack_reminder_channel" class="regular-text"
                       value="<?php echo esc_attr( $settings['slack_reminder_channel'] ?? '' ); ?>"
                       placeholder="#aufgaben">
                <p class="description">Slack-Channel fuer Aufgaben-Erinnerungen.</p>
            </div>
        </div>

        <div class="coh-card" style="max-width:700px">
            <h2>Integrationen</h2>

            <div class="coh-form-row">
                <label>ClickUp List ID</label>
                <input type="text" name="clickup_list_id" class="regular-text"
                       value="<?php echo esc_attr( $settings['clickup_list_id'] ?? '' ); ?>">
                <p class="description">Die ClickUp-Liste, in der Kundenprojekte erstellt werden.</p>
            </div>
        </div>

        <div class="coh-card" style="max-width:700px">
            <h2>Webhook</h2>

            <div class="coh-form-row">
                <label>Webhook-URL</label>
                <input type="text" class="regular-text" value="<?php echo esc_attr( $webhook_url ); ?>" readonly onclick="this.select()">
                <p class="description">Diese URL in Zapier/n8n/Make als Ziel konfigurieren. Sendet POST mit JSON-Body.</p>
            </div>

            <div class="coh-form-row">
                <label>Webhook Secret</label>
                <input type="text" name="webhook_secret" class="regular-text"
                       value="<?php echo esc_attr( $settings['webhook_secret'] ?? '' ); ?>"
                       placeholder="Optionaler Sicherheits-Token">
                <p class="description">Wird als <code>X-COH-Secret</code> Header erwartet. Leer = kein Schutz.</p>
            </div>

            <div class="coh-form-row">
                <h3>Webhook JSON-Format</h3>
                <pre class="coh-code-block">{
    "company_name": "Musterfirma GmbH",
    "contact_name": "Max Mustermann",
    "email": "max@musterfirma.de",
    "phone": "+49 123 456789",
    "website": "https://musterfirma.de",
    "address": "Musterstr. 1, 12345 Musterstadt",
    "package_type": "SEO",
    "industry": "E-Commerce",
    "monthly_volume": 3000,
    "start_date": "2026-02-17",
    "notes": "Empfehlung von Firma XY"
}</pre>
            </div>
        </div>

        <p>
            <button type="submit" name="coh_save_settings" class="button button-primary button-hero">Einstellungen speichern</button>
        </p>
    </form>
</div>
