
//SCRIPT FOR DADJOKES
const jokeEl = document.getElementById("joke")
const jokeBTN = document.getElementById("jokeBtn")

jokeBTN.addEventListener('click', generateJoke)

generateJoke()

//OPTION 1 USING .then()
// function generateJoke() {
//     const config = {
//         headers:{
//             'Accept': 'application/json'
//             } }
//     fetch('https://icanhazdadjoke.com', config)
//     .then((res) => res.json())
//     .then((data) => jokeEl.innerHTML = data.joke)
// }

//OPTION 2 USING ASYNC/AWAIT
async function generateJoke() {
    const config = {
        headers:{
            'Accept': 'application/json'
            } }

    const response = await fetch('https://icanhazdadjoke.com', config)
    const data = await response.json()
    jokeEl.innerHTML = data.joke
}


//SCRIPT FOR LOG FILE UPLOAD
// JavaScript to update the file name display
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');

fileInput.addEventListener('change', function() {
    if (fileInput.files.length > 0) {
        fileName.textContent = fileInput.files[0].name;
    } else {
        fileName.textContent = 'No file chosen';
    }
}