// Two kinds of hover help.
//
// 1. Cards in the results area, for the explanatory text behind the numbered
//    steps, the run button, the predefined reforms, DEVMOD background and the
//    tab descriptions. They follow the results card, but pin themselves to the
//    top of the viewport when it has been scrolled past, so they are always
//    fully visible. Clicking "DEVMOD info" or the tab description keeps that
//    card open, which makes the links inside it reachable.
//
// 2. Small tooltips beside a parameter, for units and other qualifications that
//    would otherwise lengthen every label.
(function () {
    var CARD_BY_TRIGGER = {
        'preset-tax-button': 'tax',
        'preset-benefits-button': 'benefits',
        'step-1-header': 'step1',
        'step-2-header': 'step2',
        'run-button': 'run',
        'view-devmod-button': 'devmod',
        'tab-info-button': 'tabinfo'
    };
    // Only the two reading-heavy cards pin on click; the other triggers have
    // their own job to do (running the model, applying a preset) and a pinned
    // card would sit over the results afterwards
    var PINNABLE = {'view-devmod-button': 1, 'tab-info-button': 1};
    // How long the pointer has to rest on a trigger before its card appears.
    // The run button gets much longer: people park the pointer there on their
    // way to clicking it, and do not want a card in the way.
    var CARD_DELAY = {'default': 400, 'run': 1100};
    var FADE_OUT = 140;                   // matches the CSS animation
    var TIP_DELAY = 450;
    var pinned = null;
    var openKey = null;
    var showTimer = null;
    var hideTimer = null;
    var tipTimer = null;
    var tipEl = null;

    // ---- results-area cards -------------------------------------------------

    function cards() {
        return Array.prototype.slice.call(document.querySelectorAll('.hovercard'));
    }

    function place(container) {
        var wrapper = document.getElementById('results-content-wrapper');
        var card = document.querySelector('.results-card');
        if (!wrapper || !card) return;
        var box = card.getBoundingClientRect();
        var anchor = wrapper.getBoundingClientRect();
        // Pin to the top of the window once the results area has scrolled up
        if (anchor.top < 12) {
            container.style.position = 'fixed';
            container.style.top = '12px';
            container.style.left = (box.left + 16) + 'px';
            container.style.width = (box.width - 32) + 'px';
            container.style.right = 'auto';
        } else {
            container.style.position = '';
            container.style.top = '';
            container.style.left = '';
            container.style.width = '';
            container.style.right = '';
        }
    }

    function showCard(key) {
        var container = document.querySelector('.hovercard-container');
        if (!container) return;
        clearTimeout(showTimer);
        clearTimeout(hideTimer);
        openKey = key;
        cards().forEach(function (c) { c.hidden = (c.id !== 'hovercard-' + key); });
        container.classList.remove('hovercard-closing');
        container.classList.toggle('hovercard-open', !!key);
        if (key) place(container);
    }

    // Wait for the pointer to settle before opening; switching from one card to
    // another is immediate, since the reader is already looking at that corner
    function requestCard(key) {
        clearTimeout(hideTimer);
        if (openKey === key) return;
        clearTimeout(showTimer);
        if (openKey) { showCard(key); return; }
        var delay = CARD_DELAY[key] || CARD_DELAY['default'];
        showTimer = setTimeout(function () { showCard(key); }, delay);
    }

    function requestHide() {
        clearTimeout(showTimer);
        if (!openKey) return;
        var container = document.querySelector('.hovercard-container');
        if (!container) return;
        clearTimeout(hideTimer);
        container.classList.add('hovercard-closing');
        hideTimer = setTimeout(function () { showCard(null); }, FADE_OUT);
    }

    function triggerFor(target) {
        if (!target || !target.closest) return null;
        var el = target.closest('[id]');
        while (el) {
            if (CARD_BY_TRIGGER[el.id]) return CARD_BY_TRIGGER[el.id];
            el = el.parentElement && el.parentElement.closest ?
                el.parentElement.closest('[id]') : null;
        }
        return null;
    }

    document.addEventListener('mouseover', function (event) {
        if (pinned) return;              // a pinned card owns the area until dismissed
        var key = triggerFor(event.target);
        if (key) requestCard(key);
        else if (!event.target.closest || !event.target.closest('.hovercard')) requestHide();
    });
    document.addEventListener('mouseleave', function () {
        if (!pinned) requestHide();
    });
    document.addEventListener('focusin', function (event) {
        var key = triggerFor(event.target);
        if (key) requestCard(key);
    });
    document.addEventListener('focusout', function () {
        if (!pinned) requestHide();           // keyboard users leaving a trigger
    });
    document.addEventListener('click', function (event) {
        var el = event.target.closest ? event.target.closest('[id]') : null;
        var key = triggerFor(event.target);
        var pinnable = key && el && PINNABLE[el.id];
        if (pinnable) {
            pinned = (pinned === key) ? null : key;
            showCard(pinned || key);
        } else if (key) {
            pinned = null;
            // starting a run closes the help so the results are not covered;
            // applying a preset leaves its card up, since it lists what changed
            showCard(el && el.id === 'run-button' ? null : key);
        } else if (pinned && (!event.target.closest || !event.target.closest('.hovercard'))) {
            pinned = null;
            showCard(null);
        }
    });
    window.addEventListener('scroll', function () {
        var container = document.querySelector('.hovercard-container');
        if (container && container.classList.contains('hovercard-open')) place(container);
    }, {passive: true});
    window.addEventListener('resize', function () {
        var container = document.querySelector('.hovercard-container');
        if (container && container.classList.contains('hovercard-open')) place(container);
    });

    // ---- small tooltips beside a parameter ---------------------------------

    function hideTip() {
        clearTimeout(tipTimer);
        if (tipEl) tipEl.classList.remove('param-tooltip-visible');
    }

    function showTip(el) {
        if (!tipEl) {
            tipEl = document.createElement('div');
            tipEl.className = 'param-tooltip';
            document.body.appendChild(tipEl);
        }
        tipEl.textContent = el.getAttribute('data-tip');
        tipEl.classList.add('param-tooltip-visible');
        var r = el.getBoundingClientRect();
        var t = tipEl.getBoundingClientRect();
        // beside the label by default, above it when there is no room to the right
        var left = r.right + 10;
        var top = r.top + r.height / 2 - t.height / 2;
        if (left + t.width > window.innerWidth - 8) {
            left = Math.max(8, r.left);
            top = r.top - t.height - 6;
        }
        tipEl.style.left = Math.round(left) + 'px';
        tipEl.style.top = Math.round(Math.max(8, top)) + 'px';
    }

    document.addEventListener('mouseover', function (event) {
        var el = event.target.closest ? event.target.closest('[data-tip]') : null;
        clearTimeout(tipTimer);
        if (!el) { hideTip(); return; }
        tipTimer = setTimeout(function () { showTip(el); }, TIP_DELAY);
    });
    document.addEventListener('mouseout', function (event) {
        if (event.target.closest && event.target.closest('[data-tip]')) hideTip();
    });
    window.addEventListener('scroll', hideTip, {passive: true});
})();
