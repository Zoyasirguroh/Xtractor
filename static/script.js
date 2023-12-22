    let BaseData = '';
    let responseData = {};

    function change() {
        document.getElementById("splash-screen").style.display = 'none';
        document.getElementById("initial-page").style.display = 'flex';
    }

    setInterval(change, 3000);

    document.getElementById('browseButton').addEventListener('click', function() {
        document.getElementById('fileInput').click();
    });

    function handleCancle() {
        document.getElementById('empty-pdf').style.display = 'flex';
        document.getElementById('pdfViewer').style.display = 'none';
        document.getElementById('file-upload-div').style.display = 'flex';
        document.getElementById('file-details-div').style.display = 'none';
        document.getElementById('table-data').style.display = 'none';
        document.getElementById('drop-area').style.display = 'flex';
        document.getElementById('upload-section').style.display = 'flex';
    }

    document.getElementById('fileInput').addEventListener('change', function(event) {
      const fileInfo = document.getElementById('fileInfo');
      const Size = document.getElementById('fileSize');

      const file = event.target.files[0];
      const fileSize = file.size;
      const fileName = file.name;

      const fileSizeMB = fileSize / (1024 ** 2);

      if(file && fileName !== ''){

        const reader = new FileReader();
        reader.readAsDataURL(file);

        reader.onload = function(e) {
          renderBase64PDF(e.target.result);
          BaseData={"file_path": e.target.result};
        //   console.log(e.target.result, 'reader')
        };

        document.getElementById('file-details').style.display = 'flex';
        document.getElementById('empty-pdf').style.display = 'none';
        document.getElementById('pdfViewer').style.display = 'flex';
        document.getElementById('back').style.display = 'flex';
        document.getElementById('file-upload-div').style.display = 'none';
        document.getElementById('file-details-div').style.display = 'flex';
        fileInfo.innerHTML = fileName;
        Size.innerHTML = fileSizeMB;
      }

    });
    function getCSRFToken() {
      const cookieString = document.cookie;
    
      if (cookieString) {
        const cookieValue = cookieString
          .split('; ')
          .find(row => row.startsWith('csrftoken='))
          ?.split('=')[1];
    
        return cookieValue;
      }
    
      return null; // or handle the absence of the cookie in your specific way
    }
    
    
    function XtractData() {
      document.getElementById('upload-section').style.display = 'none';
      document.getElementById('table-data').style.display = 'flex';
      document.getElementById('loader').style.display = 'flex';
  
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
  
      fetch('/upload_file/', {
          method: 'POST',
          body: formData,
          headers: {
              'X-CSRFToken': getCSRFToken(),  // Replace with the function to get your CSRF token
          },
      })
      .then(response => response.json())  // Parse the JSON data
      .then(data => {
        console.log(data);  // Log the parsed JSON data
        document.getElementById('loader').style.display = 'none';
    
        // Now you can use the 'data' variable to access the JSON data
        const tableBody = document.querySelector('#data-table tbody');
        tableBody.innerHTML = '';  // Clear existing table data
    
        for (const key in data) {
          const rowData = data[key];
          const row = document.createElement('tr');
    
          const keyCell = document.createElement('td');
          keyCell.textContent = rowData.key;
          keyCell.style.color = '#4A525A';
    
          const valueCell = document.createElement('td');
          valueCell.textContent = rowData.value;
          valueCell.style.color = '#053C77';
    
          row.appendChild(keyCell);
          row.appendChild(valueCell);
    
          tableBody.appendChild(row);
        }
      })
      .catch(error => {
        document.getElementById('loader').style.display = 'none';
        // Handle error
      });
    }

    // Function to render PDF from base64
    function renderBase64PDF(base64Data) {
      const iframe = document.createElement('iframe');
      iframe.style.width = '100%';
      iframe.style.height = '100%';
      document.getElementById('pdfViewer').appendChild(iframe);

      iframe.src = base64Data; // Set base64 data as the source for the iframe
    }

        // const JsonData = {
        // "0": {
        //     "key": "Share Allocations",
        //     "value": " "
        // },
        // "1": {
        //     "key": "Number of Shares",
        //     "value": "130324685"
        // },
        // "2": {
        //     "key": "Shareholder Name",
        //     "value": "Teledimo Proprietary Limited"
        // },
        // "3": {
        //     "key": "Extract generated as at 15 November 2023 12:20 PM CAT",
        //     "value": "Page 4 of 4"
        // }
        // };

        // const tableBody = document.querySelector('#data-table tbody');

        // for (const key in JsonData) {
        // const rowData = JsonData[key];
        // const row = document.createElement('tr');

        // const keyCell = document.createElement('td');
        // keyCell.textContent = rowData.key;
        // keyCell.style.color = '#4A525A';

        // const valueCell = document.createElement('td');
        // valueCell.textContent = rowData.value;
        // valueCell.style.color = '#053C77';

        // row.appendChild(keyCell);
        // row.appendChild(valueCell);

        // tableBody.appendChild(row);
        // }
