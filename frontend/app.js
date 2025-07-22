async function askStoic() {
  const input = document.getElementById("questionInput");
  const question = input.value.trim();
  const answerBox = document.getElementById("answerBox");

  if (!question) {
    answerBox.innerText = "Please enter a question.";
    return;
  }

  answerBox.innerText = "Thinking...";

  try {
    const response = await fetch("http://127.0.0.1:5000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    const data = await response.json();
    if (data.answer) {
      answerBox.innerText = data.answer;
    } else {
      answerBox.innerText = data.error || "No answer received.";
    }
  } catch (err) {
    answerBox.innerText = "An error occurred. Please try again.";
    console.error(err);
  }
}
