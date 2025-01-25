alert("Hi, I'm here")

const checkbox = document.getElementById("myCheckbox");

checkbox.addEventListener("click", function() {
  // Code to execute when the checkbox is clicked
  if (this.checked) {
    console.log("Checkbox is checked");
  } else {
    console.log("Checkbox is unchecked");
  }
});
