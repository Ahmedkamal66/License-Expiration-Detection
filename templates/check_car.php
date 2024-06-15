<?php
// Ensure that car_number is set in POST data
if (!isset($_POST['car_number'])) {
    echo "Error: No car number provided";  // Return an error if no data is found
    exit(1);  // Exit with error code
}

$car_number = $_POST['car_number'];  // Get the car number from POST data

// Database connection (adjust with your details)
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "cars";

// Create a connection to the database
$conn = new mysqli($servername, $username, $password, $dbname);

// Check for connection errors
if ($conn->connect_error) {
    echo "Error: Connection failed: " . $conn->connect_error;  // Inform about the connection error
    exit(1);  // Exit with error code
}

// SQL query to check if the car number exists
$sql = "SELECT * FROM car WHERE Number_plate = ?";  // Use parameterized query

// Prepare the SQL statement
$stmt = $conn->prepare($sql);

// Check if the statement preparation was successful
if (!$stmt) {
    echo "Error: SQL statement preparation failed";  // Inform about statement preparation failure
    exit(1);  // Exit with error code
}

// Bind the parameter and execute the query
$stmt->bind_param("s", $car_number);  // Bind the car number as a string
$stmt->execute();

// Get the result of the query
$result = $stmt->get_result();

// Check if the car number exists in the database
if ($result->num_rows > 0) {
    echo "car_found";  // If found, return "car_found"
} else {
    echo "car_not_found";  // If not found, return "car_not_found"
}

// Close the database connection
$conn->close();
?>
