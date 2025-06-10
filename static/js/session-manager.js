/**
 * Resume Screener - Session Manager
 * Handles client-side session storage using localStorage
 */

const SessionManager = {
  /**
   * Set a session value
   * @param {string} key - The key to store
   * @param {any} value - The value to store
   */
  set: (key, value) => {
    try {
      // Make sure key has the prefix
      const prefixedKey = key.startsWith('rs_') ? key : `rs_${key}`;
      localStorage.setItem(prefixedKey, JSON.stringify(value));
    } catch (e) {
      console.error("Error storing session data:", e);
    }
  },

  /**
   * Get a session value
   * @param {string} key - The key to retrieve
   * @param {any} defaultValue - Default value if key doesn't exist
   * @returns {any} The stored value or defaultValue if not found
   */
  get: (key, defaultValue = null) => {
    try {
      // Make sure key has the prefix
      const prefixedKey = key.startsWith('rs_') ? key : `rs_${key}`;
      const value = localStorage.getItem(prefixedKey);
      return value ? JSON.parse(value) : defaultValue;
    } catch (e) {
      console.error("Error retrieving session data:", e);
      return defaultValue;
    }
  },

  /**
   * Remove a session value
   * @param {string} key - The key to remove
   */
  remove: (key) => {
    try {
      localStorage.removeItem(key)
    } catch (e) {
      console.error("Error removing session data:", e)
    }
  },

  /**
   * Clear all session data
   */
  clear: () => {
    try {
      localStorage.clear()
    } catch (e) {
      console.error("Error clearing session data:", e)
    }
  },

  /**
   * Get all session data as an object
   * @returns {Object} All session data
   */
  getAll: function () {
    const data = {}
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key.startsWith("rs_")) {
          // Only get Resume Screener data
          data[key.replace("rs_", "")] = this.get(key)
        }
      }
    } catch (e) {
      console.error("Error getting all session data:", e)
    }
    return data
  },

  /**
   * Send session data to server
   * @param {string} endpoint - API endpoint to send data to
   * @param {Object} data - Data to send (defaults to all session data)
   * @returns {Promise} Promise resolving to the server response
   */
  syncToServer: async function (endpoint, data = null) {
    const sessionData = data || this.getAll();
    sessionData.session_id = this.getSessionId();

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(sessionData),
      });

      return await response.json();
    } catch (e) {
      console.error("Error syncing session data to server:", e);
      return { status: "error", message: e.message };
    }
  },

  /**
   * Generate a unique session ID
   * @returns {string} A UUID v4 string
   */
  generateSessionId: () =>
    "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0
      const v = c === "x" ? r : (r & 0x3) | 0x8
      return v.toString(16)
    }),

  /**
   * Initialize a new session
   * @returns {string} The new session ID
   */
  initSession: function () {
    const sessionId = this.generateSessionId()
    this.set("rs_session_id", sessionId)
    return sessionId
  },

  /**
   * Get the current session ID or create a new one
   * @returns {string} The session ID
   */
  getSessionId: function () {
    let sessionId = this.get("rs_session_id")
    if (!sessionId) {
      sessionId = this.initSession()
    }
    return sessionId
  },
}

// Initialize when the script loads
document.addEventListener("DOMContentLoaded", () => {
  // Ensure we have a session ID
  SessionManager.getSessionId()

  // Add session ID to all forms as a hidden field
  const forms = document.querySelectorAll("form")
  forms.forEach((form) => {
    // Check if the form already has a session_id field
    if (!form.querySelector('input[name="session_id"]')) {
      const sessionIdInput = document.createElement("input")
      sessionIdInput.type = "hidden"
      sessionIdInput.name = "session_id"
      sessionIdInput.value = SessionManager.getSessionId()
      form.appendChild(sessionIdInput)
    }
  })
})
