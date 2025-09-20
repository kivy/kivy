<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Cartoon ABC Game</title>
  <style>
    body {
      margin: 0;
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      background: linear-gradient(skyblue, lightgreen);
      font-family: sans-serif;
      overflow: hidden;
    }
    .game {
      text-align: center;
    }
    .letter {
      font-size: 120px;
      font-weight: bold;
      cursor: pointer;
      animation: bounce 2s infinite;
    }
    @keyframes bounce {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-20px); }
    }
    .character {
      font-size: 60px;
      animation: float 4s infinite;
    }
    @keyframes float {
      0% { transform: translateY(0); }
      50% { transform: translateY(-15px); }
      100% { transform: translateY(0); }
    }
    .cloud {
      position: absolute;
      top: 50px;
      left: -200px;
      font-size: 80px;
      animation: drift 30s linear infinite;
    }
    @keyframes drift {
      0% { left: -200px; }
      100% { left: 110%; }
    }
    button {
      margin: 10px;
      padding: 10px 20px;
      font-size: 20px;
      border-radius: 12px;
      border: none;
      background: orange;
      cursor: pointer;
    }
    .hint {
      font-size: 28px;
      margin-top: 20px;
      font-weight: bold;
      color: darkblue;
    }
  </style>
</head>
<body>
  <div class="cloud">☁️</div>
  <div class="game">
    <div id="character" class="character">😀</div>
    <div id="letter" class="letter">A</div>
    <button onclick="sayLetter()">Speak</button>
    <button onclick="nextLetter()">Next</button>
    <button onclick="showHint()">Hint</button>
    <div id="hint" class="hint"></div>
  </div>

  <script>
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
    let index = 0;

    function sayLetter(){
      const letter = letters[index];
      const utter = new SpeechSynthesisUtterance(letter);
      window.speechSynthesis.speak(utter);
      animateLetter();
    }

    function animateLetter(){
      const letterDiv = document.getElementById('letter');
      letterDiv.style.transform = 'scale(1.3)';
      setTimeout(()=> letterDiv.style.transform='scale(1)', 300);
    }

    function nextLetter(){
      index = (index + 1) % letters.length;
      document.getElementById('letter').textContent = letters[index];
      document.getElementById('hint').textContent = '';
    }

    function showHint(){
      document.getElementById('hint').textContent = 'Boy';
    }
  </script>
</body>
</html>
