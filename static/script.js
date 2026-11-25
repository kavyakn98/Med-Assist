
// ==========================================
// MEDASSIST - MAIN JAVASCRIPT
// ==========================================


// HTML ELEMENTS
const medicineForm = document.getElementById("medicineForm");
const medicineList = document.getElementById("medicineList");
const reminderList = document.getElementById("reminderList");


// ==========================================
// 1. ADD MEDICINE
// ==========================================

if (medicineForm) {

    medicineForm.addEventListener("submit", async function(event) {

        event.preventDefault();

        const name = document.getElementById("medicineName").value.trim();
        const dosage = document.getElementById("dosage").value.trim();
        const time = document.getElementById("medicineTime").value;

        if (!name || !dosage || !time) {
            alert("Please fill in all medicine details.");
            return;
        }

        try {

            const response = await fetch("/add_medicine", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: name,
                    dosage: dosage,
                    time: time
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || "Unable to add medicine.");
            }

            alert("Medicine added successfully!");

            medicineForm.reset();

            loadMedicines();

        } catch (error) {

            console.error("Add medicine error:", error);
            alert(error.message);

        }

    });

}


// ==========================================
// 2. LOAD MEDICINES FROM DATABASE
// ==========================================

async function loadMedicines() {

    try {

        const response = await fetch("/get_medicines");

        if (!response.ok) {
            throw new Error("Unable to load medicines.");
        }

        const medicines = await response.json();

        displayMedicines(medicines);
        displayReminders(medicines);
        updateDashboard(medicines);
        updateReminderSummary(medicines);

    } catch (error) {

        console.error("Loading error:", error);

        if (medicineList) {
            medicineList.innerHTML = "<p>Unable to load medicines.</p>";
        }

        if (reminderList) {
            reminderList.innerHTML = "<p>Unable to load reminders.</p>";
        }

    }

}


// ==========================================
// 3. DISPLAY MEDICINES
// ==========================================

function displayMedicines(medicines) {

    if (!medicineList) {
        return;
    }

    medicineList.innerHTML = "";

    if (medicines.length === 0) {

        medicineList.innerHTML = `
            <div class="schedule-placeholder">
                <div class="placeholder-icon">💊</div>
                <h3>No medicines added yet</h3>
                <p>Add your first medicine using the form above.</p>
            </div>
        `;

        return;
    }

    medicines.forEach(function(medicine) {

        const card = document.createElement("div");
        card.className = "medicine-card";

        const details = document.createElement("div");

        const name = document.createElement("h3");
        name.textContent = medicine.name;

        const dosage = document.createElement("p");
        dosage.textContent = "Dosage: " + medicine.dosage;

        const time = document.createElement("p");
        time.textContent = "Reminder Time: " + medicine.time;

        const status = document.createElement("p");
        status.textContent = "Status: " + medicine.status;

        details.appendChild(name);
        details.appendChild(dosage);
        details.appendChild(time);
        details.appendChild(status);

        const deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";

        deleteButton.addEventListener("click", function() {
            deleteMedicine(medicine.id);
        });

        card.appendChild(details);
        card.appendChild(deleteButton);

        medicineList.appendChild(card);

    });

}


// ==========================================
// 4. DISPLAY REMINDERS
// ==========================================

function displayReminders(medicines) {

    if (!reminderList) {
        return;
    }

    reminderList.innerHTML = "";

    if (medicines.length === 0) {

        reminderList.innerHTML = `
            <div class="schedule-placeholder">
                <div class="placeholder-icon">🔔</div>
                <h3>No reminders available</h3>
                <p>Add medicines and their reminder times to see your schedule here.</p>
                <a href="/medicines" class="secondary-link">+ Add Medicine</a>
            </div>
        `;

        return;
    }

    const sortedMedicines = [...medicines].sort(function(a, b) {
        return a.time.localeCompare(b.time);
    });

    sortedMedicines.forEach(function(medicine) {

        const card = document.createElement("div");
        card.className = "reminder-card";

        const details = document.createElement("div");

        const name = document.createElement("h3");
        name.textContent = medicine.name;

        const dosage = document.createElement("p");
        dosage.textContent = "Dosage: " + medicine.dosage;

        const time = document.createElement("p");
        time.textContent = "Scheduled time: " + medicine.time;

        const status = document.createElement("p");
        status.textContent = "Status: " + medicine.status;

        details.appendChild(name);
        details.appendChild(dosage);
        details.appendChild(time);
        details.appendChild(status);

        const timeLabel = document.createElement("span");
        timeLabel.textContent = medicine.time;
        timeLabel.style.color = "#159e96";
        timeLabel.style.fontWeight = "700";
        timeLabel.style.fontSize = "12px";

        card.appendChild(details);
        card.appendChild(timeLabel);

        reminderList.appendChild(card);

    });

}


// ==========================================
// 5. DELETE MEDICINE
// ==========================================

async function deleteMedicine(id) {

    const confirmDelete = confirm(
        "Are you sure you want to delete this medicine?"
    );

    if (!confirmDelete) {
        return;
    }

    try {

        const response = await fetch("/delete_medicine/" + id, {
            method: "DELETE"
        });

        if (!response.ok) {
            throw new Error("Unable to delete medicine.");
        }

        alert("Medicine deleted successfully!");

        loadMedicines();

    } catch (error) {

        console.error("Delete error:", error);
        alert(error.message);

    }

}


// ==========================================
// 6. UPDATE MEDICINE STATUS
// ==========================================

async function updateMedicineStatus(id, status) {

    try {

        const response = await fetch("/update_status/" + id, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                status: status
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Unable to update status.");
        }

        loadMedicines();

    } catch (error) {

        console.error("Status update error:", error);
        alert(error.message);

    }

}


// ==========================================
// 7. UPDATE DASHBOARD COUNTS
// ==========================================

function updateDashboard(medicines) {

    const totalElement = document.getElementById("totalCount");
    const takenElement = document.getElementById("takenCount");
    const upcomingElement = document.getElementById("upcomingCount");
    const missedElement = document.getElementById("missedCount");

    const total = medicines.length;

    const taken = medicines.filter(function(medicine) {
        return medicine.status === "Taken";
    }).length;

    const missed = medicines.filter(function(medicine) {
        return medicine.status === "Missed";
    }).length;

    const upcoming = medicines.filter(function(medicine) {
        return medicine.status === "Upcoming" ||
               medicine.status === "Snoozed";
    }).length;

    if (totalElement) totalElement.textContent = total;
    if (takenElement) takenElement.textContent = taken;
    if (upcomingElement) upcomingElement.textContent = upcoming;
    if (missedElement) missedElement.textContent = missed;

}


// ==========================================
// 8. UPDATE REMINDER PAGE COUNTS
// ==========================================

function updateReminderSummary(medicines) {

    const totalElement = document.getElementById("reminderTotal");
    const upcomingElement = document.getElementById("reminderUpcoming");

    const total = medicines.length;

    const upcoming = medicines.filter(function(medicine) {
        return medicine.status === "Upcoming" ||
               medicine.status === "Snoozed";
    }).length;

    if (totalElement) {
        totalElement.textContent = total;
    }

    if (upcomingElement) {
        upcomingElement.textContent = upcoming;
    }

}


// ==========================================
// 9. ALARM BUTTON ACTIONS
// ==========================================

// These buttons will be connected to the
// active alarm when we build the alarm engine.

const takenButton = document.getElementById("takenButton");
const snoozeButton = document.getElementById("snoozeButton");
const missedButton = document.getElementById("missedButton");


// ==========================================
// 10. INITIAL WEBSITE LOAD
// ==========================================

loadMedicines();
