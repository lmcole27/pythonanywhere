document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('question-form');
    const responseContainer = document.getElementById('response');

    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        const formData = new FormData(form);
        responseContainer.innerHTML = '';
        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });

        let question = document.getElementById('question').value;
        document.getElementById('question').value = '';
        document.getElementById('questionAsked').innerText = question;
        document.getElementById('questionAskedHeader').style.display = "block";
        document.getElementById('responseHeader').style.display = "block";
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value);
            responseContainer.innerHTML = buffer;
        }
        
        console.log(responseContainer.innerText);

        fetch('/assistantAPI/response', {
            method: 'POST', // HTTP method
            headers: {
                'Content-Type': 'application/json' // Tells the server you're sending JSON
            },
            credentials: 'include',
            body: JSON.stringify({ message: responseContainer.innerText  }) // The data to send
        })
        .then(response => response.json()) // Convert response to JSON
        .then(data => console.log('Success:', data)) // Handle success
        .catch(error => console.error('Error:', error)); // Handle errors
    });
});



window.onload = () => {
    fetch('/assistantAPI/get_session', {
        method: 'GET', // HTTP method
        headers: {
            'Content-Type': 'application/json' // Tells the server you're sending JSON
        },
        credentials: 'include',
        //body: JSON.stringify('xyz')
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          const token = data.token
          showOutput(`Welcome Guest ${token}`);
          closePopup();
        } else {
            showPopup();
        }
})
};

function showPopup() {
    document.getElementById('popup').style.display = 'flex';
    document.body.classList.add('modal-open');
    document.getElementById('main-content').classList.remove('active');
};

function closePopup() {
    document.getElementById('popup').style.display = 'none';
    document.body.classList.remove('modal-open');
    document.getElementById('main-content').classList.add('active');
};

function showOutput(data) {
    document.getElementById('output').textContent = 
      typeof data === 'string' ? data : JSON.stringify(data, null, 2);
  }

function setGuestToken() {
    fetch('/assistantAPI/set_session',{
        method: 'GET',
        headers:{'Content-Type': 'application/json'},
        credentials: 'include',
        //body:JSON.stringify('xyz')
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const token = data.token
            showOutput(`Welcome Guest ${token}`);
            closePopup();
          } else {
              showPopup();
          }
        }
    )
}