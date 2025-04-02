function checkStatus(processId) {
  const statusUrl = "{{ url_for('get_status', process_id='') }}" + processId;

  fetch(statusUrl)
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "completed") {
        displayResults(data.results);
        document.getElementById("loading").style.display = "none";
      } else if (data.status === "error") {
        document.getElementById("error-message").textContent = data.message;
        document.getElementById("loading").style.display = "none";
      } else {
        setTimeout(() => checkStatus(processId), 1000);
      }
    })
    .catch((error) => {
      document.getElementById("loading").style.display = "none";
      document.getElementById("error-message").textContent =
        "エラーが発生しました: " + error.message;
    });
}

function displayResults(results) {
  const resultsContainer = document.getElementById("results-container");
  let tableHtml = `
    <h3>結果一覧</h3>
    <table border="1">
      <tr>
        <th>質問</th>
        <th>回答</th>
        <th>回答時間 (秒)</th>
        <th>情報ソース</th>
      </tr>
  `;

  results.forEach((result) => {
    tableHtml += `
      <tr>
        <td>${result.question}</td>
        <td>${result.answer}</td>
        <td>${result.time_taken}</td>
        <td>
          ${result.sources
            .map(
              (source) =>
                `<a href="${source.url_link}" target="_blank">${source.title}</a><br>`
            )
            .join("")}
        </td>
      </tr>
    `;
  });

  tableHtml += "</table>";
  resultsContainer.innerHTML = tableHtml;
}

document.getElementById("uploadForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const fileInput = document.querySelector('input[type="file"]');
  if (!fileInput.files.length) {
    alert("ファイルを選択してください。");
    return;
  }

  const file = fileInput.files[0];
  const reader = new FileReader();

  reader.onload = function (event) {
    const fileContent = event.target.result;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("text", fileContent);

    const loading = document.getElementById("loading");
    const errorMessage = document.getElementById("error-message");
    const resultsContainer = document.getElementById("results-container");

    loading.style.display = "block";
    errorMessage.textContent = "";
    resultsContainer.innerHTML = "";

    fetch("{{ url_for('test_upload') }}", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "error") {
          loading.style.display = "none";
          errorMessage.textContent = JSON.stringify(data.message);
        } else if (data.status === "processing") {
          checkStatus(data.process_id);
          setTimeout(() => checkStatus(data.process_id), 1000);
        }
      })
      .catch((error) => {
        loading.style.display = "none";
        errorMessage.textContent = "エラーが発生しました: " + error.message;
      });
  };

  reader.readAsText(file);
});
