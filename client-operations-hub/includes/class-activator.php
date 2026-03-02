<?php
/**
 * Plugin activation: creates database tables.
 *
 * @package ClientOperationsHub
 */

namespace COH;

defined( 'ABSPATH' ) || exit;

class Activator {

    /**
     * Run on activation.
     */
    public static function activate() {
        self::create_tables();
        self::seed_task_templates();
        self::add_capabilities();
        update_option( 'coh_version', COH_VERSION );
        flush_rewrite_rules();
    }

    /**
     * Create all custom database tables.
     */
    private static function create_tables() {
        global $wpdb;

        $charset_collate = $wpdb->get_charset_collate();

        require_once ABSPATH . 'wp-admin/includes/upgrade.php';

        // --- Clients ---
        $table_clients = $wpdb->prefix . 'coh_clients';
        $sql_clients   = "CREATE TABLE {$table_clients} (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            company_name varchar(255) NOT NULL,
            contact_name varchar(255) NOT NULL,
            email varchar(255) NOT NULL,
            phone varchar(50) DEFAULT '',
            website varchar(255) DEFAULT '',
            address text DEFAULT NULL,
            package_type varchar(100) NOT NULL DEFAULT '',
            industry varchar(100) DEFAULT '',
            monthly_volume decimal(12,2) DEFAULT 0,
            tier varchar(20) NOT NULL DEFAULT 'bronze',
            health_score int(3) DEFAULT 0,
            status varchar(20) NOT NULL DEFAULT 'active',
            start_date date NOT NULL,
            notes text DEFAULT NULL,
            hubspot_deal_id varchar(100) DEFAULT '',
            clickup_project_id varchar(100) DEFAULT '',
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_status (status),
            KEY idx_tier (tier),
            KEY idx_start_date (start_date)
        ) {$charset_collate};";

        dbDelta( $sql_clients );

        // --- Task Templates ---
        $table_templates = $wpdb->prefix . 'coh_task_templates';
        $sql_templates   = "CREATE TABLE {$table_templates} (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            title varchar(255) NOT NULL,
            description text DEFAULT NULL,
            task_type varchar(20) NOT NULL DEFAULT 'manual',
            day_offset int(5) NOT NULL DEFAULT 0,
            priority varchar(20) NOT NULL DEFAULT 'normal',
            phase int(2) NOT NULL DEFAULT 1,
            sort_order int(5) NOT NULL DEFAULT 0,
            conditions longtext DEFAULT NULL,
            is_active tinyint(1) NOT NULL DEFAULT 1,
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_phase (phase),
            KEY idx_day_offset (day_offset)
        ) {$charset_collate};";

        dbDelta( $sql_templates );

        // --- Tasks (per client) ---
        $table_tasks = $wpdb->prefix . 'coh_tasks';
        $sql_tasks   = "CREATE TABLE {$table_tasks} (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            client_id bigint(20) unsigned NOT NULL,
            template_id bigint(20) unsigned DEFAULT NULL,
            title varchar(255) NOT NULL,
            description text DEFAULT NULL,
            task_type varchar(20) NOT NULL DEFAULT 'manual',
            due_date date NOT NULL,
            assigned_to bigint(20) unsigned DEFAULT NULL,
            priority varchar(20) NOT NULL DEFAULT 'normal',
            status varchar(20) NOT NULL DEFAULT 'pending',
            phase int(2) NOT NULL DEFAULT 1,
            sort_order int(5) NOT NULL DEFAULT 0,
            completed_at datetime DEFAULT NULL,
            completed_by bigint(20) unsigned DEFAULT NULL,
            notes text DEFAULT NULL,
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_client_id (client_id),
            KEY idx_status (status),
            KEY idx_due_date (due_date),
            KEY idx_assigned_to (assigned_to),
            KEY idx_client_status (client_id, status)
        ) {$charset_collate};";

        dbDelta( $sql_tasks );

        // --- API Keys (encrypted) ---
        $table_api_keys = $wpdb->prefix . 'coh_api_keys';
        $sql_api_keys   = "CREATE TABLE {$table_api_keys} (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            service_name varchar(100) NOT NULL,
            service_label varchar(255) NOT NULL DEFAULT '',
            api_key_encrypted text NOT NULL,
            api_key_iv varchar(255) NOT NULL DEFAULT '',
            extra_fields longtext DEFAULT NULL,
            status varchar(20) NOT NULL DEFAULT 'untested',
            last_tested datetime DEFAULT NULL,
            created_by bigint(20) unsigned NOT NULL,
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY idx_service_name (service_name)
        ) {$charset_collate};";

        dbDelta( $sql_api_keys );

        // --- API Key Audit Log ---
        $table_audit = $wpdb->prefix . 'coh_api_key_audit';
        $sql_audit   = "CREATE TABLE {$table_audit} (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            api_key_id bigint(20) unsigned NOT NULL,
            action varchar(50) NOT NULL,
            user_id bigint(20) unsigned NOT NULL,
            details text DEFAULT NULL,
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_api_key_id (api_key_id),
            KEY idx_user_id (user_id)
        ) {$charset_collate};";

        dbDelta( $sql_audit );

        // --- Activity Log ---
        $table_activity = $wpdb->prefix . 'coh_activity_log';
        $sql_activity   = "CREATE TABLE {$table_activity} (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            client_id bigint(20) unsigned NOT NULL,
            activity_type varchar(50) NOT NULL,
            title varchar(255) NOT NULL,
            description text DEFAULT NULL,
            meta longtext DEFAULT NULL,
            user_id bigint(20) unsigned DEFAULT NULL,
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_client_id (client_id),
            KEY idx_activity_type (activity_type),
            KEY idx_created_at (created_at)
        ) {$charset_collate};";

        dbDelta( $sql_activity );

        // --- Reminders ---
        $table_reminders = $wpdb->prefix . 'coh_reminders';
        $sql_reminders   = "CREATE TABLE {$table_reminders} (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            task_id bigint(20) unsigned DEFAULT NULL,
            client_id bigint(20) unsigned NOT NULL,
            channel varchar(20) NOT NULL DEFAULT 'email',
            subject varchar(255) NOT NULL DEFAULT '',
            message text DEFAULT NULL,
            scheduled_at datetime NOT NULL,
            sent_at datetime DEFAULT NULL,
            status varchar(20) NOT NULL DEFAULT 'pending',
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_status_scheduled (status, scheduled_at),
            KEY idx_task_id (task_id),
            KEY idx_client_id (client_id)
        ) {$charset_collate};";

        dbDelta( $sql_reminders );

        // --- Health Score History ---
        $table_health = $wpdb->prefix . 'coh_health_history';
        $sql_health   = "CREATE TABLE {$table_health} (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            client_id bigint(20) unsigned NOT NULL,
            score int(3) NOT NULL,
            tier varchar(20) NOT NULL DEFAULT 'bronze',
            details longtext DEFAULT NULL,
            recorded_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_client_id (client_id),
            KEY idx_recorded_at (recorded_at)
        ) {$charset_collate};";

        dbDelta( $sql_health );
    }

    /**
     * Seed default task templates based on 11-phase process.
     */
    private static function seed_task_templates() {
        global $wpdb;

        $table = $wpdb->prefix . 'coh_task_templates';

        // Only seed if table is empty.
        $count = (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$table}" );
        if ( $count > 0 ) {
            return;
        }

        $templates = array(
            // Phase 1: Immediate Post-Sale (Tag 0)
            array(
                'title'       => 'CEO-Willkommensanruf',
                'description' => 'Persoenlicher Anruf des CEOs/Geschaeftsfuehrers beim neuen Kunden. Dank aussprechen, Begeisterung zeigen, erste Fragen klaeren. Buyer\'s Remorse vorbeugen.',
                'task_type'   => 'manual',
                'day_offset'  => 0,
                'priority'    => 'high',
                'phase'       => 1,
                'sort_order'  => 10,
            ),
            array(
                'title'       => 'Loom-Video aufnehmen',
                'description' => 'Personalisiertes Willkommensvideo (2-3 Min) aufnehmen. Kunde beim Namen ansprechen, auf Firma eingehen, naechste Schritte erklaeren.',
                'task_type'   => 'manual',
                'day_offset'  => 0,
                'priority'    => 'high',
                'phase'       => 1,
                'sort_order'  => 20,
            ),
            array(
                'title'       => 'Handgeschriebene Karte #1 schreiben',
                'description' => 'Willkommenskarte von Hand schreiben. Persoenliche Note, Bezug auf das Gespraech nehmen. An Kundenadresse versenden.',
                'task_type'   => 'manual',
                'day_offset'  => 0,
                'priority'    => 'normal',
                'phase'       => 1,
                'sort_order'  => 30,
            ),
            array(
                'title'       => 'Willkommens-Email senden',
                'description' => 'Email-Template 01 personalisieren und senden. Enthaelt: Quick Engagement Element, Loom-Video-Link, naechste Schritte.',
                'task_type'   => 'semi-automatic',
                'day_offset'  => 0,
                'priority'    => 'high',
                'phase'       => 1,
                'sort_order'  => 40,
            ),

            // Phase 2: Welcome Package (Tag 1)
            array(
                'title'       => 'Welcome-Package zusammenstellen und versenden',
                'description' => 'Welcome-Package gemaess Tier-Level zusammenstellen: Branded Notizbuch, Stift, Willkommenskarte, ggf. Buch oder Spezial-Item. Tracking-Nummer notieren.',
                'task_type'   => 'manual',
                'day_offset'  => 1,
                'priority'    => 'high',
                'phase'       => 2,
                'sort_order'  => 50,
            ),

            // Phase 3: Team-Vorstellung (Tag 1-2)
            array(
                'title'       => 'Team-Vorstellungs-Email senden',
                'description' => 'Email-Template 02 personalisieren und senden. Teamfotos, Rollen, direkter Kontakt. Zeigt dem Kunden wer fuer ihn arbeitet.',
                'task_type'   => 'semi-automatic',
                'day_offset'  => 2,
                'priority'    => 'normal',
                'phase'       => 3,
                'sort_order'  => 60,
            ),

            // Phase 4: Discovery & Onboarding (Tag 2-5)
            array(
                'title'       => 'Discovery Call planen',
                'description' => 'Calendly-Link an Kunden senden fuer Discovery Call. Fragen aus dem Onboarding-Fragebogen als Vorbereitung nutzen.',
                'task_type'   => 'manual',
                'day_offset'  => 2,
                'priority'    => 'high',
                'phase'       => 4,
                'sort_order'  => 70,
            ),
            array(
                'title'       => 'Onboarding-Fragebogen senden',
                'description' => 'Email-Template 03 personalisieren und senden. Enthaelt Onboarding-Checklist und Asset-Anforderungen (Zugaenge, Logos, Brand Guide).',
                'task_type'   => 'semi-automatic',
                'day_offset'  => 3,
                'priority'    => 'high',
                'phase'       => 4,
                'sort_order'  => 80,
            ),

            // Phase 5: Audit & Strategy (Tag 7-10)
            array(
                'title'       => 'Marketing-Audit durchfuehren',
                'description' => 'Vollstaendiges Audit der aktuellen Marketing-Aktivitaeten: Website, SEO, Content, Social, Ads. Ergebnisse dokumentieren.',
                'task_type'   => 'manual',
                'day_offset'  => 7,
                'priority'    => 'high',
                'phase'       => 5,
                'sort_order'  => 90,
            ),
            array(
                'title'       => 'Strategie entwickeln',
                'description' => '90-Tage-Strategie basierend auf Audit-Ergebnissen entwickeln. Quick Wins identifizieren, Roadmap erstellen.',
                'task_type'   => 'manual',
                'day_offset'  => 10,
                'priority'    => 'high',
                'phase'       => 5,
                'sort_order'  => 100,
            ),

            // Phase 6: Kickoff Meeting (Tag 14)
            array(
                'title'       => 'Kickoff-Meeting durchfuehren',
                'description' => 'Strukturiertes Kickoff gemaess Agenda-Template: Audit-Ergebnisse praesentieren, Strategie vorstellen, Meilensteine definieren, Quick Win ankuendigen.',
                'task_type'   => 'manual',
                'day_offset'  => 14,
                'priority'    => 'high',
                'phase'       => 6,
                'sort_order'  => 110,
            ),

            // Phase 7: Quick Win (Tag 21)
            array(
                'title'       => 'Quick Win liefern',
                'description' => 'Ersten sichtbaren Erfolg liefern und dokumentieren. Ergebnis per Email/Call mit dem Kunden teilen und feiern.',
                'task_type'   => 'manual',
                'day_offset'  => 21,
                'priority'    => 'high',
                'phase'       => 7,
                'sort_order'  => 120,
            ),

            // Phase 8: 30-Tage Check-in (Tag 30)
            array(
                'title'       => 'Erste-Ergebnisse-Email senden',
                'description' => 'Email-Template 04 personalisieren und senden. Erste Resultate feiern, Fortschritt zeigen, naechste Schritte ankuendigen.',
                'task_type'   => 'semi-automatic',
                'day_offset'  => 25,
                'priority'    => 'normal',
                'phase'       => 8,
                'sort_order'  => 125,
            ),
            array(
                'title'       => '30-Tage Check-in Call',
                'description' => 'Strukturierter Call: Zufriedenheit abfragen, erste Ergebnisse besprechen, Erwartungen abgleichen, offene Fragen klaeren.',
                'task_type'   => 'manual',
                'day_offset'  => 30,
                'priority'    => 'high',
                'phase'       => 8,
                'sort_order'  => 130,
            ),

            // Phase 9: Ongoing Value (Tag 42-60)
            array(
                'title'       => 'Handgeschriebene Karte #2 schreiben',
                'description' => 'Zweite persoenliche Karte nach ca. 6 Wochen. Bezug auf erreichte Meilensteine oder persoenliche Anekdote.',
                'task_type'   => 'manual',
                'day_offset'  => 42,
                'priority'    => 'normal',
                'phase'       => 9,
                'sort_order'  => 140,
            ),
            array(
                'title'       => 'Insights-Email + Feedback senden',
                'description' => 'Email-Template 05 personalisieren und senden. Branchenspezifische Insights teilen, Feedback einholen.',
                'task_type'   => 'semi-automatic',
                'day_offset'  => 60,
                'priority'    => 'normal',
                'phase'       => 9,
                'sort_order'  => 150,
            ),

            // Phase 10: Pre-Review (Tag 84)
            array(
                'title'       => 'Handgeschriebene Karte #3 schreiben',
                'description' => 'Dritte persoenliche Karte vor dem 90-Tage-Review. Vorfreude auf gemeinsame Auswertung ausdruecken.',
                'task_type'   => 'manual',
                'day_offset'  => 84,
                'priority'    => 'normal',
                'phase'       => 10,
                'sort_order'  => 160,
            ),

            // Phase 11: 90-Tage Review (Tag 90)
            array(
                'title'       => 'NPS-Umfrage + Review-Email senden',
                'description' => 'Email-Template 06 personalisieren und senden. NPS-Umfrage eingebettet, Review-Meeting ankuendigen, Testimonial anfragen.',
                'task_type'   => 'semi-automatic',
                'day_offset'  => 88,
                'priority'    => 'high',
                'phase'       => 11,
                'sort_order'  => 170,
            ),
            array(
                'title'       => '90-Tage Review Meeting',
                'description' => 'Umfassendes Review: Alle KPIs praesentieren, ROI berechnen, Erfolge feiern, naechste 90 Tage planen. Testimonial-Anfrage bei Zufriedenheit.',
                'task_type'   => 'manual',
                'day_offset'  => 90,
                'priority'    => 'high',
                'phase'       => 11,
                'sort_order'  => 180,
            ),
        );

        foreach ( $templates as $template ) {
            $wpdb->insert( $table, array_merge( $template, array( 'is_active' => 1 ) ) );
        }
    }

    /**
     * Add custom capabilities to administrator role.
     */
    private static function add_capabilities() {
        $admin = get_role( 'administrator' );
        if ( ! $admin ) {
            return;
        }

        $caps = array(
            'coh_manage_clients',
            'coh_manage_tasks',
            'coh_manage_api_keys',
            'coh_view_dashboard',
            'coh_manage_settings',
        );

        foreach ( $caps as $cap ) {
            $admin->add_cap( $cap );
        }
    }
}
