import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const chatEndRef = useRef(null);

  useEffect(() => {
    loadDocuments();

    const savedMessages = localStorage.getItem("chatHistory");

    if (savedMessages) {
      setMessages(JSON.parse(savedMessages));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(
      "chatHistory",
      JSON.stringify(messages)
    );

    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });

  }, [messages]);

  const loadDocuments = async () => {
    try {
      const res = await fetch(
        "http://127.0.0.1:8000/documents"
      );

      const data = await res.json();

      setDocuments(data.documents);

      if (
        data.documents.length > 0 &&
        !selectedDoc
      ) {
        setSelectedDoc(data.documents[0]);
      }

    } catch (err) {
      console.log(err);
    }
  };

  const uploadFile = async () => {

    if (!file) {
      alert("Select PDF first");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {

      const res = await fetch(
        "http://127.0.0.1:8000/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await res.json();

      if (data.success) {

        alert(
          `${data.filename} uploaded successfully`
        );

        loadDocuments();

      } else {
        alert(data.error);
      }

    } catch {
      alert("Upload failed");
    }
  };

  const askQuestion = async () => {

    if (!question.trim()) return;

    if (!selectedDoc) {
      alert("Select a document");
      return;
    }

    const time = new Date().toLocaleTimeString(
      [],
      {
        hour: "2-digit",
        minute: "2-digit",
      }
    );

    const userMsg = {
      role: "user",
      text: question,
      time,
    };

    setMessages((prev) => [...prev, userMsg]);

    setLoading(true);

    try {

      const res = await fetch(
        "http://127.0.0.1:8000/ask",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            question,
            selected_doc: selectedDoc,
          }),
        }
      );

      const data = await res.json();

      const aiMsg = {
        role: "ai",
        text: data.answer,
        time: new Date().toLocaleTimeString(
          [],
          {
            hour: "2-digit",
            minute: "2-digit",
          }
        ),
      };

      setMessages((prev) => [
        ...prev,
        aiMsg,
      ]);

      setQuestion("");

    } catch {

      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: "Failed to contact AI",
          time: new Date().toLocaleTimeString(),
        },
      ]);
    }

    setLoading(false);
  };

  const clearChat = () => {

    localStorage.removeItem(
      "chatHistory"
    );

    setMessages([]);

    fetch(
      "http://127.0.0.1:8000/clear",
      {
        method: "POST",
      }
    );
  };

  const handleEnter = (e) => {
    if (e.key === "Enter") {
      askQuestion();
    }
  };

  return (
    <div className="app">

      <div className="sidebar">

        <div className="logo">
          DocuMind AI
        </div>

        <div className="sidebarTitle">
          Documents
        </div>

        {documents.map((doc, index) => (
          <div
            key={index}
            onClick={() =>
              setSelectedDoc(doc)
            }
            className={
              selectedDoc === doc
                ? "docItem activeDoc"
                : "docItem"
            }
          >
            📄 {doc}
          </div>
        ))}

      </div>

      <div className="main">

        <div className="header">

          <div>
            <h1>
              Enterprise Knowledge Assistant
            </h1>

            <p>
              Selected:
              {" "}
              <strong>
                {selectedDoc || "None"}
              </strong>
            </p>
          </div>

          <button
            onClick={clearChat}
          >
            Clear Chat
          </button>

        </div>

        <div className="uploadSection">

          <input
            type="file"
            accept=".pdf"
            onChange={(e) =>
              setFile(e.target.files[0])
            }
          />

          <button
            onClick={uploadFile}
          >
            Upload PDF
          </button>

        </div>

        <div className="chatBox">

          {messages.map(
            (msg, index) => (
              <div
                key={index}
                className={
                  msg.role === "user"
                    ? "userWrapper"
                    : "aiWrapper"
                }
              >
                <div
                  className={
                    msg.role === "user"
                      ? "userMessage"
                      : "aiMessage"
                  }
                >
                  {msg.text}
                </div>

                <div className="timeStamp">
                  {msg.time}
                </div>

              </div>
            )
          )}

          {loading && (
            <div className="typing">

              <span></span>
              <span></span>
              <span></span>

            </div>
          )}

          <div ref={chatEndRef}></div>

        </div>

        <div className="inputArea">

          <input
            value={question}
            onChange={(e) =>
              setQuestion(
                e.target.value
              )
            }
            onKeyDown={handleEnter}
            placeholder="Ask a question..."
          />

          <button
            onClick={askQuestion}
          >
            Send
          </button>

        </div>

      </div>

    </div>
  );
}

export default App;