(() => {
    const form = document.getElementById("passwordResetForm");
    if (!form) {
        return;
    }

    const status = document.getElementById("passwordResetStatus");
    const submitButton = document.getElementById("passwordResetSubmit");
    const originalButtonText = submitButton.textContent;

    function showStatus(message, kind) {
        status.hidden = false;
        status.className = `password-reset-status alert alert-${kind} mt-3`;
        status.textContent = message;
    }

    function getErrorMessage(payload) {
        if (payload.detail) {
            return payload.detail;
        }
        for (const value of Object.values(payload)) {
            if (Array.isArray(value) && value.length) {
                return value[0];
            }
        }
        return "We couldn't process your request. Please try again.";
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        status.hidden = true;
        submitButton.disabled = true;
        submitButton.textContent = "Sending...";

        try {
            const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
            const response = await fetch(form.dataset.apiUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfInput ? csrfInput.value : "",
                },
                body: JSON.stringify({
                    email: form.querySelector("#id_email").value.trim(),
                }),
            });

            let payload;
            try {
                payload = await response.json();
            } catch {
                throw new Error("The server returned an invalid response.");
            }

            if (!response.ok) {
                throw new Error(getErrorMessage(payload));
            }

            showStatus(payload.detail, "success");
            window.location.assign(form.dataset.successUrl);
        } catch (error) {
            showStatus(error.message || "Unable to contact the server. Please try again.", "danger");
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    });
})();
