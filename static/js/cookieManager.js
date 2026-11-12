/**
 * Cookie & Security Token Manager
 * Handles CSRF token extraction, persistence, and secure cookie lifecycle.
 */
class CookieManager {
    static get(name) {
        const nameEQ = encodeURIComponent(name) + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return decodeURIComponent(c.substring(nameEQ.length, c.length));
        }
        return null;
    }

    static set(name, value, days = 7, path = '/') {
        let expires = "";
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = encodeURIComponent(name) + "=" + encodeURIComponent(value || "") + expires + "; path=" + path + "; SameSite=Lax";
    }

    static delete(name, path = '/') {
        document.cookie = encodeURIComponent(name) + "=; Max-Age=-99999999; path=" + path;
    }

    static getCSRFToken() {
        return this.get('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    static getAuthHeaders(includeContentType = true) {
        const headers = {
            'X-CSRFToken': this.getCSRFToken(),
            'Accept': 'application/json'
        };
        const jwtToken = localStorage.getItem('access_token');
        if (jwtToken) {
            headers['Authorization'] = 'Bearer ' + jwtToken;
        }
        if (includeContentType) {
            headers['Content-Type'] = 'application/json';
        }
        return headers;
    }
}

window.CookieManager = CookieManager;

