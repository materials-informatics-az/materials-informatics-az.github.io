/* ---------------------------------------------------------------------------
   Click-to-load embeds.

   The group's apps are hosted on their own origins, so each embed is a full
   cross-origin page load. Nothing loads until the reader asks for it: markup
   ships a poster button, and this swaps in the iframe on activation.

   Because the frame is cross-origin, the parent cannot measure its content —
   the height comes from CSS (--embed-height) and never from the app.
   --------------------------------------------------------------------------- */

(function () {
  "use strict";

  function load(container) {
    var src = container.dataset.embedSrc;
    var title = container.dataset.embedTitle || "Embedded application";
    var stage = container.querySelector(".embed-stage");
    if (!src || !stage || container.dataset.embedLoaded) return;

    var frame = document.createElement("iframe");
    frame.src = src;
    frame.title = title;
    frame.loading = "lazy";
    frame.allow = "fullscreen";
    frame.setAttribute("referrerpolicy", "no-referrer-when-downgrade");

    // Replace the poster only. The bar above it keeps the app's name and the
    // open-full-screen link, which the reader still needs once it has loaded.
    container.dataset.embedLoaded = "true";
    stage.replaceChildren(frame);
  }

  document.addEventListener("click", function (event) {
    var poster = event.target.closest("[data-embed-load]");
    if (!poster) return;
    var container = poster.closest("[data-embed-src]");
    if (container) load(container);
  });
})();

/* ---------------------------------------------------------------------------
   Newsletter form.

   Posts to the endpoint in content/site.yml. Without an endpoint the form is
   inert and says so rather than pretending to have worked. The response is
   never trusted to be JSON — a misconfigured endpoint returns HTML.
   --------------------------------------------------------------------------- */

(function () {
  "use strict";

  var form = document.querySelector("[data-newsletter]");
  if (!form) return;

  var status = form.parentNode.querySelector("[data-newsletter-status]");
  var button = form.querySelector("button");

  function say(message, tone) {
    if (!status) return;
    status.textContent = message;
    status.dataset.tone = tone;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var endpoint = form.getAttribute("action");
    if (!endpoint) {
      say("Sign-up is not connected yet — email us and we will add you.", "error");
      return;
    }

    var email = form.querySelector("input[type=email]").value.trim();
    if (!email) return;

    button.disabled = true;
    say("Signing you up…", "pending");

    fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        // Formspree and similar endpoints redirect to a thank-you page unless
        // asked for JSON. Harmless for providers that always return JSON.
        Accept: "application/json",
      },
      body: "email=" + encodeURIComponent(email),
    })
      .then(function (response) {
        if (!response.ok) throw new Error(String(response.status));
        form.reset();
        say("You are on the list. Thank you.", "ok");
      })
      .catch(function () {
        say("That did not go through. Try again, or email us.", "error");
      })
      .then(function () {
        button.disabled = false;
      });
  });
})();

/* ---------------------------------------------------------------------------
   Copy BibTeX.

   Every entry on the publications page carries its own BibTeX in a data
   attribute, so a copy is instant and needs no network. The button reports what
   happened in its own label: a clipboard write can be refused (an insecure
   origin, a permissions policy, a browser that has neither API) and silently
   doing nothing is the one outcome a reader cannot recover from.
   --------------------------------------------------------------------------- */

(function () {
  "use strict";

  var RESET_MS = 1600;

  // navigator.clipboard needs a secure context; file:// and plain http do not
  // have one, and this page is read locally often enough to matter.
  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      // Off-screen but still selectable; display:none is not.
      area.style.position = "fixed";
      area.style.top = "-1000px";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      var ok = false;
      try {
        ok = document.execCommand("copy");
      } catch (error) {
        ok = false;
      }
      document.body.removeChild(area);
      ok ? resolve() : reject(new Error("copy refused"));
    });
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-bibtex]");
    if (!button) return;

    var label = button.querySelector("[data-cite-label]");
    if (!label) return;

    // A second click while the confirmation is showing restarts the timer
    // rather than stacking a second one that would clear the label early.
    clearTimeout(button._citeTimer);

    function settle(state, text) {
      button.dataset.state = state;
      label.textContent = text;
      button._citeTimer = setTimeout(function () {
        delete button.dataset.state;
        label.textContent = "cite";
      }, RESET_MS);
    }

    copy(button.dataset.bibtex).then(
      function () {
        settle("done", "copied");
      },
      function () {
        settle("error", "select it");
        // Nothing was copied, so leave the reader something to copy by hand.
        window.prompt("Copy the BibTeX entry:", button.dataset.bibtex);
      }
    );
  });
})();
