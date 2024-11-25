import React, { useState } from 'react';
import { MathComponent } from 'mathjax-react'; // Correct import
import Tesseract from 'tesseract.js'; // Import Tesseract.js
import './App.css';

function App() {
  const [userInput, setUserInput] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentBotText, setCurrentBotText] = useState('');
  const [typingIndex, setTypingIndex] = useState(0);
  const [ocrText, setOcrText] = useState(''); // For OCR text
  const [imageFile, setImageFile] = useState(null); // For image file

  const handleInputChange = (event) => {
    setUserInput(event.target.value);
  };

  const handleSendMessage = async () => {
    if (!userInput.trim()) return;

    const newMessage = { sender: 'user', text: userInput };
    setChatHistory([...chatHistory, newMessage]);

    setUserInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/chatbot/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input: userInput }),
      });

      const data = await response.json();
      if (data.error) {
        addBotMessage(`Error: ${data.error}`);
      } else {
        simulateTypingEffect(data.prediction);
      }
    } catch (error) {
      addBotMessage('An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const addBotMessage = (text) => {
    setChatHistory((prev) => [...prev, { sender: 'bot', text }]);
    setCurrentBotText('');
    setTypingIndex(0);
  };

  const simulateTypingEffect = (fullText) => {
    setCurrentBotText('');
    setTypingIndex(0);

    const intervalId = setInterval(() => {
      setTypingIndex((prevIndex) => {
        const nextIndex = prevIndex + 1;
        setCurrentBotText(fullText.slice(0, nextIndex));

        if (nextIndex === fullText.length) {
          clearInterval(intervalId);
          addBotMessage(fullText);
        }

        return nextIndex;
      });
    }, 50); // Typing speed in milliseconds per character
  };

  // Function to handle image change
  const handleImageChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setImageFile(file);
      // Start OCR processing on the image
      processImage(file);
    }
  };

  // Function to process the image using Tesseract.js
  const processImage = (image) => {
    Tesseract.recognize(
      image,
      'eng', // Language code for English
      {
        logger: (m) => console.log(m), // Optional: logs progress
      },
    ).then(({ data: { text } }) => {
      setOcrText(text); // Store OCR text
      simulateTypingEffect(text); // Display OCR text using typing effect
    });
  };

  const renderMessage = (message) => {
    if (message.sender === 'bot') {
      const splitMessage = message.text.split(
        /(\$\$.*?\$\$|\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\])/g,
      );

      return (
        <span
          style={{
            whiteSpace: 'normal',
            display: 'inline-flex',
            flexWrap: 'wrap',
            alignItems: 'center',
          }}>
          {splitMessage.map((part, index) => {
            if (!part) return null;

            if (part.startsWith('\\(') && part.endsWith('\\)')) {
              const latexText = part.replace(/\\\(|\\\)/g, '');
              return (
                <React.Fragment key={index}>
                  <MathComponent tex={latexText} display={false} />
                  &nbsp;
                </React.Fragment>
              );
            }

            if (part.startsWith('\\[') && part.endsWith('\\]')) {
              const latexText = part.replace(/\\\[|\\\]/g, '');
              return (
                <React.Fragment key={index}>
                  <MathComponent tex={latexText} display={true} />
                  &nbsp;
                </React.Fragment>
              );
            }

            if (part.startsWith('$') && part.endsWith('$')) {
              const isBlock = part.startsWith('$$') && part.endsWith('$$');
              const latexText = part.replace(/\$\$|\$/g, '');
              return (
                <React.Fragment key={index}>
                  <MathComponent tex={latexText} display={isBlock} />
                  &nbsp;
                </React.Fragment>
              );
            }

            return <React.Fragment key={index}>{part}&nbsp;</React.Fragment>;
          })}
        </span>
      );
    }

    return <p>{message.text}</p>;
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Jeebot Preparation</h1>

        <div className="chat-container">
          <div className="chat-history">
            {chatHistory.map((message, index) => (
              <div
                key={index}
                className={`chat-message ${
                  message.sender === 'user' ? 'user' : 'bot'
                }`}>
                {renderMessage(message)}
              </div>
            ))}
            {/* Display typing effect */}
            {currentBotText && (
              <div className="chat-message bot">
                {renderMessage({ sender: 'bot', text: currentBotText })}
              </div>
            )}
          </div>

          <div className="chat-input">
            <input
              type="text"
              value={userInput}
              onChange={handleInputChange}
              placeholder="Type your message..."
            />
            <button onClick={handleSendMessage} disabled={isLoading}>
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>

          <div className="image-upload">
            <input type="file" accept="image/*" onChange={handleImageChange} />
          </div>

          {ocrText && (
            <div>
              <h3>OCR Result:</h3>
              <p>{ocrText}</p>
            </div>
          )}
        </div>
      </header>
    </div>
  );
}

export default App;
