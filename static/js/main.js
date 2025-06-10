/**
 * Resume Screener Premium - Main JavaScript
 * Provides interactive features for the premium resume screening application
 */

document.addEventListener("DOMContentLoaded", () => {
  // Initialize all components
  initFileUpload()
  initPrioritySliders()
  initFormValidation()
  initCandidateSelection()
  initTooltips()
  initProgressBars()
  initAnimations()
})

/**
 * Initialize file upload functionality
 */
function initFileUpload() {
  // File upload preview for job description
  const jobDescriptionInput = document.getElementById("job_description")
  if (jobDescriptionInput) {
    jobDescriptionInput.addEventListener("change", function () {
      updateFilePreview(this, "job-file-preview")
    })
  }

  // File upload preview for resumes
  const resumesInput = document.getElementById("resumes")
  if (resumesInput) {
    resumesInput.addEventListener("change", function () {
      const fileCount = this.files.length
      const fileList = document.createElement("div")
      fileList.className = "mt-3"

      if (fileCount > 0) {
        const fileHeader = document.createElement("p")
        fileHeader.className = "fw-bold"
        fileHeader.textContent = `Selected ${fileCount} file(s):`
        fileList.appendChild(fileHeader)

        const fileNames = document.createElement("ul")
        fileNames.className = "file-list"

        for (let i = 0; i < fileCount; i++) {
          const item = document.createElement("li")
          item.className = "file-item"

          item.innerHTML = `
            <div class="file-item-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5L14 4.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5h-2z"/>
                <path d="M4.5 12.5A.5.5 0 0 1 5 12h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5zm0-2A.5.5 0 0 1 5 10h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5zm0-2A.5.5 0 0 1 5 8h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5zm0-2A.5.5 0 0 1 5 6h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5z"/>
              </svg>
            </div>
            <div class="file-item-name">${this.files[i].name}</div>
          `
          fileNames.appendChild(item)
        }

        fileList.appendChild(fileNames)
      }

      // Remove previous list if exists
      const previousList = this.parentNode.querySelector("div.mt-3")
      if (previousList) {
        previousList.remove()
      }

      // Add new list
      if (fileCount > 0) {
        this.parentNode.appendChild(fileList)
      }
    })
  }

  // Drag and drop functionality
  const dropZones = document.querySelectorAll(".file-upload")
  dropZones.forEach((zone) => {
    zone.addEventListener("dragover", function (e) {
      e.preventDefault()
      this.classList.add("border-primary")
      this.style.backgroundColor = "rgba(58, 89, 152, 0.05)"
    })

    zone.addEventListener("dragleave", function (e) {
      e.preventDefault()
      this.classList.remove("border-primary")
      this.style.backgroundColor = ""
    })

    zone.addEventListener("drop", function (e) {
      e.preventDefault()
      this.classList.remove("border-primary")
      this.style.backgroundColor = ""

      const input = this.querySelector('input[type="file"]')
      if (input) {
        input.files = e.dataTransfer.files

        // Trigger change event
        const event = new Event("change", { bubbles: true })
        input.dispatchEvent(event)
      }
    })
  })
}

/**
 * Update file preview
 * @param {HTMLInputElement} input - File input element
 * @param {string} previewId - ID of preview element
 */
function updateFilePreview(input, previewId) {
  const preview = document.getElementById(previewId)
  if (!preview) return

  if (input.files && input.files.length > 0) {
    const fileName = input.files[0].name
    preview.textContent = fileName
    preview.classList.remove("d-none")
  } else {
    preview.textContent = ""
    preview.classList.add("d-none")
  }
}

/**
 * Initialize priority sliders
 */
function initPrioritySliders() {
  const priorityInputs = document.querySelectorAll('input[type="number"][min="1"][max="10"]')
  priorityInputs.forEach((input) => {
    input.addEventListener("change", function () {
      const value = Number.parseInt(this.value)
      if (value >= 1 && value <= 10) {
        // Change background color based on priority
        const alpha = value / 10
        this.style.backgroundColor = `rgba(58, 89, 152, ${alpha})`
        this.style.color = value > 5 ? "white" : "black"
      } else {
        this.style.backgroundColor = ""
        this.style.color = ""
      }
    })

    // Trigger change event to apply initial styling
    input.dispatchEvent(new Event("change"))
  })
}

/**
 * Initialize form validation
 */
function initFormValidation() {
  const forms = document.querySelectorAll(".needs-validation")

  Array.from(forms).forEach((form) => {
    form.addEventListener(
      "submit",
      (event) => {
        if (!form.checkValidity()) {
          event.preventDefault()
          event.stopPropagation()
        }

        form.classList.add("was-validated")
      },
      false,
    )
  })
}

/**
 * Initialize candidate selection in results table
 */
function initCandidateSelection() {
  const candidateRows = document.querySelectorAll(".candidate-row")
  const candidateDetails = document.getElementById("candidate-details")

  candidateRows.forEach((row) => {
    row.addEventListener("click", function () {
      // Remove selected class from all rows
      candidateRows.forEach((r) => r.classList.remove("selected"))

      // Add selected class to clicked row
      this.classList.add("selected")

      // Update candidate details if available
      if (candidateDetails) {
        const candidateName = this.getAttribute("data-candidate")
        const overallScore = this.getAttribute("data-score")

        // Update details
        const nameElement = candidateDetails.querySelector(".candidate-name")
        const scoreElement = candidateDetails.querySelector(".candidate-score")

        if (nameElement) nameElement.textContent = candidateName
        if (scoreElement) {
          scoreElement.textContent = `${overallScore}%`

          // Update score color
          const score = Number.parseFloat(overallScore)
          if (score >= 80) {
            scoreElement.className = "candidate-score text-success"
          } else if (score >= 60) {
            scoreElement.className = "candidate-score text-warning"
          } else {
            scoreElement.className = "candidate-score text-danger"
          }
        }

        // Show details with animation
        candidateDetails.classList.remove("d-none")
        candidateDetails.style.opacity = "0"
        candidateDetails.style.transform = "translateY(10px)"

        setTimeout(() => {
          candidateDetails.style.opacity = "1"
          candidateDetails.style.transform = "translateY(0)"
        }, 10)
      }
    })
  })
}

/**
 * Initialize tooltips
 */
function initTooltips() {
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  if (tooltipTriggerList.length > 0) {
    // Declare bootstrap variable
    const bootstrap = window.bootstrap

    Array.from(tooltipTriggerList).forEach((tooltipTriggerEl) => {
      new bootstrap.Tooltip(tooltipTriggerEl)
    })
  }
}

/**
 * Initialize progress bars
 */
function initProgressBars() {
  const progressBars = document.querySelectorAll(".progress-bar")
  progressBars.forEach((bar) => {
    const value = bar.getAttribute("aria-valuenow")
    bar.style.width = `${value}%`

    // Set color based on value
    if (value >= 80) {
      bar.classList.add("bg-success")
    } else if (value >= 60) {
      bar.classList.add("bg-warning")
    } else {
      bar.classList.add("bg-danger")
    }
  })
}

/**
 * Initialize animations
 */
function initAnimations() {
  // Animate cards on page load
  const cards = document.querySelectorAll(".card")
  cards.forEach((card, index) => {
    card.style.opacity = "0"
    card.style.transform = "translateY(20px)"

    setTimeout(
      () => {
        card.style.transition = "opacity 0.5s ease, transform 0.5s ease"
        card.style.opacity = "1"
        card.style.transform = "translateY(0)"
      },
      100 + index * 100,
    )
  })

  // Animate step numbers
  const stepNumbers = document.querySelectorAll(".step-number")
  stepNumbers.forEach((number, index) => {
    setTimeout(
      () => {
        number.style.transition = "transform 0.3s ease"
        number.style.transform = "scale(1.1)"

        setTimeout(() => {
          number.style.transform = "scale(1)"
        }, 300)
      },
      500 + index * 200,
    )
  })
}

/**
 * Format a number as a percentage
 * @param {number} value - Value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage
 */
function formatPercentage(value, decimals = 1) {
  return value.toFixed(decimals) + "%"
}

/**
 * Show loading spinner
 * @param {string} containerId - ID of container element
 * @param {string} message - Loading message
 */
function showLoading(containerId, message = "Processing...") {
  const container = document.getElementById(containerId)
  if (!container) return

  const spinner = document.createElement("div")
  spinner.className = "text-center my-5"
  spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2">${message}</p>
    `

  container.innerHTML = ""
  container.appendChild(spinner)
}

/**
 * Hide loading spinner
 * @param {string} containerId - ID of container element
 */
function hideLoading(containerId) {
  const container = document.getElementById(containerId)
  if (!container) return

  const spinner = container.querySelector(".spinner-border")
  if (spinner) {
    spinner.parentNode.remove()
  }
}

/**
 * Show alert message
 * @param {string} containerId - ID of container element
 * @param {string} message - Alert message
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {boolean} dismissible - Whether the alert can be dismissed
 */
function showAlert(containerId, message, type = "info", dismissible = true) {
  const container = document.getElementById(containerId)
  if (!container) return

  const alert = document.createElement("div")
  alert.className = `alert alert-${type} ${dismissible ? "alert-dismissible fade show" : ""}`
  alert.setAttribute("role", "alert")

  alert.innerHTML = message

  if (dismissible) {
    alert.innerHTML += `
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `
  }

  container.appendChild(alert)
}
