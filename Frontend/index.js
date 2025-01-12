const express = require('express');
const axios = require('axios');
// const cors = require('cors');
const app = express();
const port = 3000;

// Enable CORS for front-end communication
app.use(express.static(__dirname + "/public"));
app.use(express.urlencoded({ extended: true })); // Middleware for URL-encoded data
app.use(express.json());

app.listen(port, () => {
    console.log(`Node.js server is running on http://localhost:${port}`);
});

app.get("/", (req, res) => { //home page
  res.sendFile(__dirname + "/main.html");
});

app.post("/receive_filters", async function(req, res){
  console.log(req.body); // Logs the received data
  var filters = req.body;  // Get filters from the request

  try {
      console.log("the filters", filters)
        // Send the filter request to the Python backend
        const response = await axios.post('http://localhost:5000/filterMovies', { filters });

        // Send back the response from the Python backend
        res.json({ message: 'Filters forwarded to backend!', data: response.data });
    } catch (error) {
        console.error('Error fetching data from Python backend:', error);
        res.status(500).send('Internal Server Error');
    }
});

app.get("/clear_database", (req, res) =>{
  console.log("called clear_database, attempting to call clearDatabse")
    try {
        const response = axios.get('http://localhost:5000/clearDatabase');
        res.json({ message: 'Request has been made to clear Databse.'});
    } catch (error) {
        console.error('Could Not Clear Database due to: ', error);
        res.status(500).send('Internal Server Error');
    }
});

