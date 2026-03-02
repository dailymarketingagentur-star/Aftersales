/**
 * Client Operations Hub - Admin JavaScript
 */
(function ($) {
    'use strict';

    var api = {
        url: cohAdmin.restUrl,
        nonce: cohAdmin.nonce,

        request: function (method, endpoint, data) {
            return $.ajax({
                url: this.url + endpoint,
                method: method,
                contentType: 'application/json',
                data: data ? JSON.stringify(data) : undefined,
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-WP-Nonce', api.nonce);
                },
            });
        },
    };

    // =========================================================================
    // Complete Task
    // =========================================================================

    $(document).on('click', '.coh-complete-task', function (e) {
        e.preventDefault();
        var $btn = $(this);
        var taskId = $btn.data('task-id');

        $btn.prop('disabled', true).text('...');

        api.request('POST', 'tasks/' + taskId + '/complete', {})
            .done(function () {
                var $row = $btn.closest('tr');
                $row.find('.coh-status-badge')
                    .removeClass('coh-status--pending coh-status--in_progress')
                    .addClass('coh-status--completed')
                    .text('Completed');
                $row.removeClass('coh-row-overdue').attr('data-status', 'completed');
                $btn.closest('td').html('<small>Erledigt</small>');
            })
            .fail(function () {
                alert('Fehler beim Abschliessen der Aufgabe.');
                $btn.prop('disabled', false).text('Erledigt');
            });
    });

    // =========================================================================
    // Skip Task
    // =========================================================================

    $(document).on('click', '.coh-skip-task', function (e) {
        e.preventDefault();
        var $btn = $(this);
        var taskId = $btn.data('task-id');
        var reason = prompt('Grund fuer das Ueberspringen (optional):') || '';

        $btn.prop('disabled', true).text('...');

        api.request('POST', 'tasks/' + taskId + '/skip', { reason: reason })
            .done(function () {
                var $row = $btn.closest('tr');
                $row.find('.coh-status-badge')
                    .removeClass('coh-status--pending coh-status--in_progress')
                    .addClass('coh-status--skipped')
                    .text('Skipped');
                $row.removeClass('coh-row-overdue').attr('data-status', 'skipped');
                $btn.closest('td').html('<small>Uebersprungen</small>');
            })
            .fail(function () {
                alert('Fehler beim Ueberspringen.');
                $btn.prop('disabled', false).text('Ueberspringen');
            });
    });

    // =========================================================================
    // New Client Form
    // =========================================================================

    $(document).on('submit', '#coh-new-client-form', function (e) {
        e.preventDefault();
        var $form = $(this);
        var $btn = $form.find('[type="submit"]');

        var data = {};
        $form.serializeArray().forEach(function (field) {
            data[field.name] = field.value;
        });

        if (data.monthly_volume) {
            data.monthly_volume = parseFloat(data.monthly_volume) || 0;
        }

        $btn.prop('disabled', true).text('Wird angelegt...');

        api.request('POST', 'clients', data)
            .done(function (resp) {
                if (resp.client_id) {
                    window.location.href =
                        cohAdmin.adminUrl +
                        '?page=coh-clients&client_id=' +
                        resp.client_id;
                }
            })
            .fail(function (xhr) {
                var msg =
                    (xhr.responseJSON && xhr.responseJSON.error) ||
                    'Fehler beim Anlegen.';
                alert(msg);
                $btn.prop('disabled', false).text(
                    'Kunden anlegen & Pipeline starten'
                );
            });
    });

    // =========================================================================
    // Task Filters (client detail page)
    // =========================================================================

    $(document).on('click', '.coh-task-filter', function (e) {
        e.preventDefault();
        var $btn = $(this);
        var filter = $btn.data('filter');

        $btn.siblings().removeClass('active');
        $btn.addClass('active');

        var $rows = $btn
            .closest('.coh-card')
            .find('.coh-task-table tbody tr');

        if (filter === 'all') {
            $rows.removeClass('coh-hidden');
        } else {
            $rows.each(function () {
                var status = $(this).data('status');
                $(this).toggleClass('coh-hidden', status !== filter);
            });
        }
    });

    // =========================================================================
    // Client Search (list page)
    // =========================================================================

    $(document).on('input', '#coh-client-search', function () {
        var term = $(this).val().toLowerCase();
        var $rows = $('.coh-client-table tbody tr');

        if (!term) {
            $rows.show();
            return;
        }

        $rows.each(function () {
            var text = $(this).text().toLowerCase();
            $(this).toggle(text.indexOf(term) !== -1);
        });
    });

    // =========================================================================
    // Health Score Slider
    // =========================================================================

    $(document).on('change', '.coh-health-slider', function () {
        var $slider = $(this);
        var clientId = $slider.data('client-id');
        var score = parseInt($slider.val(), 10);

        $slider
            .closest('div')
            .find('.coh-health-score')
            .text(score + '/100')
            .attr('data-score', score);

        api.request('PUT', 'clients/' + clientId, {
            health_score: score,
        });
    });

    // =========================================================================
    // Add Note
    // =========================================================================

    $(document).on('click', '.coh-add-note-btn', function (e) {
        e.preventDefault();
        var $btn = $(this);
        var clientId = $btn.data('client-id');
        var $textarea = $('#coh-note-text');
        var text = $textarea.val().trim();

        if (!text) return;

        $btn.prop('disabled', true);

        api.request('POST', 'clients/' + clientId + '/activity', {
            title: 'Notiz',
            description: text,
        })
            .done(function () {
                $textarea.val('');
                // Add to timeline visually.
                var now = new Date();
                var dateStr =
                    String(now.getDate()).padStart(2, '0') +
                    '.' +
                    String(now.getMonth() + 1).padStart(2, '0') +
                    '.' +
                    now.getFullYear() +
                    ' ' +
                    String(now.getHours()).padStart(2, '0') +
                    ':' +
                    String(now.getMinutes()).padStart(2, '0');

                var html =
                    '<div class="coh-timeline-entry coh-activity-type--note">' +
                    '<span class="coh-timeline-date">' + dateStr + '</span>' +
                    '<strong>Notiz</strong>' +
                    '<p>' + $('<span>').text(text).html() + '</p>' +
                    '</div>';

                var $timeline = $btn.closest('.coh-card').find('.coh-timeline');
                $timeline.find('.coh-empty').remove();
                $timeline.prepend(html);
            })
            .always(function () {
                $btn.prop('disabled', false);
            });
    });

    // =========================================================================
    // API Key Vault
    // =========================================================================

    $(document).on('click', '.coh-save-api-key', function (e) {
        e.preventDefault();
        var $btn = $(this);
        var service = $btn.data('service');
        var $row = $btn.closest('tr');
        var apiKey = $row.find('.coh-api-key-field').val();

        if (!apiKey) {
            alert('Bitte API-Key eingeben.');
            return;
        }

        var data = { api_key: apiKey };

        // Check for extra fields.
        $row.find('.coh-api-extra-field').each(function () {
            var field = $(this).data('field');
            data[field] = $(this).val();
        });

        $btn.prop('disabled', true).text('...');

        api.request('POST', 'api-keys/' + service, data)
            .done(function () {
                $row.find('.coh-api-key-field')
                    .val('')
                    .attr('placeholder', 'Key gespeichert (zum Aendern neuen eingeben)');
                $row.find('.coh-api-status')
                    .removeClass('coh-api-status--not_configured coh-api-status--error coh-api-status--connected')
                    .addClass('coh-api-status--untested')
                    .text('Nicht getestet');
                $row.find('.coh-test-api-key').prop('disabled', false);
                $btn.text('Speichern');
            })
            .fail(function () {
                alert('Fehler beim Speichern.');
            })
            .always(function () {
                $btn.prop('disabled', false);
                if ($btn.text() === '...') $btn.text('Speichern');
            });
    });

    $(document).on('click', '.coh-test-api-key', function (e) {
        e.preventDefault();
        var $btn = $(this);
        var service = $btn.data('service');
        var $row = $btn.closest('tr');

        $btn.prop('disabled', true).text('Teste...');

        api.request('POST', 'api-keys/' + service + '/test', {})
            .done(function (resp) {
                var $status = $row.find('.coh-api-status');
                $status.removeClass(
                    'coh-api-status--not_configured coh-api-status--error coh-api-status--untested coh-api-status--connected'
                );

                if (resp.success) {
                    $status.addClass('coh-api-status--connected').text('Verbunden');
                } else {
                    $status.addClass('coh-api-status--error').text('Fehler');
                    alert('Verbindungsfehler: ' + resp.message);
                }
            })
            .fail(function () {
                alert('Test fehlgeschlagen.');
            })
            .always(function () {
                $btn.prop('disabled', false).text('Testen');
            });
    });

    $(document).on('click', '.coh-delete-api-key', function (e) {
        e.preventDefault();
        var $btn = $(this);
        var service = $btn.data('service');

        if (!confirm('API-Key fuer diesen Service wirklich loeschen?')) return;

        $btn.prop('disabled', true);

        api.request('DELETE', 'api-keys/' + service, {})
            .done(function () {
                location.reload();
            })
            .fail(function () {
                alert('Fehler beim Loeschen.');
                $btn.prop('disabled', false);
            });
    });

    // =========================================================================
    // Color health scores on page load
    // =========================================================================

    function colorHealthScores() {
        $('.coh-health-score').each(function () {
            var score = parseInt($(this).attr('data-score'), 10);
            if (isNaN(score)) return;

            if (score >= 50) {
                $(this).css('color', '#00a32a');
            } else if (score >= 30) {
                $(this).css('color', '#dba617');
            } else {
                $(this).css('color', '#d63638');
            }
        });
    }

    $(document).ready(function () {
        colorHealthScores();
    });
})(jQuery);
