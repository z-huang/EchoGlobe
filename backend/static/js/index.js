function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', async function () {
    const debtAddForm = document.getElementById('debtAddForm');
    const toggleHistoryBtn = document.getElementById('toggleHistoryBtn');
    const historySection = document.getElementById('historySection');
    const creditorSelect = document.getElementById('creditor');
    const debtorSelect = document.getElementById('debtor');
    const amountInput = document.getElementById('amount');
    const descriptionInput = document.getElementById('description');
    const debtRelationsTable = document.getElementById('debtRelationsTable');
    const transactionHistoryList = document.getElementById('transactionHistoryList');
    const app = new PIXI.Application();
    await app.init({
        height: 250,
        backgroundColor: 0xf4f4f4,
        resolution: window.devicePixelRatio || 1,
    });

    document.getElementById('pixiCanvasContainer').appendChild(app.view);



    fetch('/api/users/')
        .then(response => response.json())
        .then(data => {
            data.users.forEach(user => {
                let option1 = document.createElement('option');
                option1.value = user.id;
                option1.textContent = user.username;
                creditorSelect.appendChild(option1);

                let option2 = document.createElement('option');
                option2.value = user.id;
                option2.textContent = user.username;
                debtorSelect.appendChild(option2);
            });
        });

    function updateDebtRelationsTable() {
        fetch('/api/debt-relations/')
            .then(response => response.json())
            .then(data => {
                debtRelationsTable.innerHTML = `
                    <thead>
                        <tr>
                            <th>From</th>
                            <th>To</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                `;

                const tbody = debtRelationsTable.querySelector('tbody');

                data.forEach(history => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${history.from}</td>
                        <td>${history.to}</td>
                        <td>${history.amount}</td>
                    `;
                    tbody.appendChild(row);
                });

            });
    }

    function updateDebtVisualization() {
        fetch('/api/total-debts/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie("csrftoken")
            },
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            if (app.stage.children.length > 0) app.stage.removeChildren();

            const maxDebt = Math.max(...data.map(u => Math.abs(u.total_debt)), 1);
            const circles = [];

            data.forEach(user => {
                const debt = user.total_debt;
                const radius = radiusScale(debt, maxDebt);
                const color = debt < 0 ? 0x991f9f : 0x1c98a5;

                const circle = new PIXI.Graphics();
                circle.beginFill(color).drawCircle(0, 0, radius).endFill();

                const fontSize = Math.max(8, radius * 0.25);
                const label = new PIXI.Text(`${user.username}\n$${debt}`, {
                    fontFamily: 'Poppins',
                    fontSize: fontSize,
                    fill: debt < 0 ? '#fff' : '#000',
                    align: 'center'
                });

                label.anchor.set(0.5);

                const group = new PIXI.Container();
                group.addChild(circle);
                group.addChild(label);
                group.x = app.screen.width / 2 + (Math.random() * 80 - 40);
                group.y = app.screen.height / 2 + (Math.random() * 80 - 40);
                group.radius = radius;
                circles.push(group);
                app.stage.addChild(group);
            });

            resolveCircleCollisions(circles);
            scaleToFitContainer(app.stage, app.screen.width, app.screen.height);
        });
    }

    function radiusScale(debt, maxDebt, base = 1.6, scale = 14, minR = 20, maxR = 50) {
        const magnitude = -debt / maxDebt;
        return Math.min(minR + Math.pow(base, magnitude) * scale, maxR);
    }


    function resolveCircleCollisions(circles, iterations = 30) {
        for (let i = 0; i < iterations; i++) {
            for (let a = 0; a < circles.length; a++) {
                for (let b = a + 1; b < circles.length; b++) {
                    const A = circles[a], B = circles[b];
                    const dx = B.x - A.x, dy = B.y - A.y;
                    const dist = Math.hypot(dx, dy);
                    const minDist = A.radius + B.radius + 4;
                    if (dist < minDist) {
                        const angle = Math.atan2(dy, dx);
                        const shift = (minDist - dist) / 2;
                        A.x -= Math.cos(angle) * shift;
                        A.y -= Math.sin(angle) * shift;
                        B.x += Math.cos(angle) * shift;
                        B.y += Math.sin(angle) * shift;
                    }
                }
            }
        }
    }

    function scaleToFitContainer(container, maxW, maxH) {
        const bounds = container.getLocalBounds();
        const scale = Math.min(maxW / bounds.width, maxH / bounds.height, 1);
        container.scale.set(scale);
        container.x = (maxW - bounds.width * scale) / 2 - bounds.x * scale;
        container.y = (maxH - bounds.height * scale) / 2 - bounds.y * scale;
    }

    updateDebtRelationsTable();
    fetchTotalDebtTable();
    updateDebtVisualization();

    function fetchTotalDebtTable() {
        fetch('/api/total-debts/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie("csrftoken")
            },
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            const table = document.getElementById("totalDebtTable");
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Total Debt</th>
                    </tr>
                </thead>
                <tbody></tbody>
            `;

            const tbody = table.querySelector('tbody');
            data.forEach(user => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${user.username}</td>
                    <td>$${user.total_debt}</td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching total debts:', error));
    }


    debtAddForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const creditor = creditorSelect.value;
        const debtor = debtorSelect.value;
        const amount = parseInt(amountInput.value);
        const description = descriptionInput.value;

        if (creditor === debtor) {
            Swal.fire({
                icon: 'error',
                title: 'Oops...',
                text: 'From 和 To 不能是同一個人！',
                confirmButtonText: '確認',
                confirmButtonColor: '#4a90e2'
            });
            return;
        }

        if (creditor && debtor && amount) {
            fetch('/api/transactions/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie("csrftoken")
                },
                body: JSON.stringify({ creditor, debtor, amount, description })
            })
                .then(response => response.json())
                .then(data => {
                    updateDebtRelationsTable();
                    fetchTransactionHistory();
                    fetchTotalDebtTable();
                    updateDebtVisualization();
                    amountInput.value = '';
                    descriptionInput.value = '';
                });
        }
    });

    function formatDate(dateString) {
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const seconds = date.getSeconds().toString().padStart(2, '0');
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    }

    toggleHistoryBtn.addEventListener('click', function () {
        historySection.style.display = historySection.style.display === 'block' ? 'none' : 'block';
        if (historySection.style.display === 'block') {
            fetchTransactionHistory();
        }
    });

    function fetchTransactionHistory() {
        fetch('/api/transactions/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie("csrftoken")
            }
        })
            .then(response => response.json())
            .then(data => {
                transactionHistoryList.innerHTML = ''; // Clear the list before adding new data

                data.forEach(transaction => {
                    const row = document.createElement('tr');  // Create a new row for each transaction

                    row.innerHTML = `
                        <td>${transaction.creditor}</td>
                        <td>${transaction.debtor}</td>
                        <td>${transaction.amount}</td>
                        <td>${transaction.description}</td>
                        <td>${formatDate(transaction.created_at)}</td>
                    `;

                    transactionHistoryList.appendChild(row);  // Append the new row to the table
                });
            })
            .catch(error => {
                console.error('Error fetching transaction history:', error);
            });
    }
});