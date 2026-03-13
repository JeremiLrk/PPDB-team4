import React, { useState } from "react";

const Admin = () => {
  // State voor formulieren
  const [clubName, setClubName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [message, setMessage] = useState({ text: "", type: "" });

  // 1. Club aanmaken
  const handleCreateClub = (e) => {
    e.preventDefault();
    if (!clubName) return;

    // TODO: Vervang door API call: fetch('/api/clubs', { method: 'POST', body: ... })
    console.log(`Club aangemaakt: ${clubName}`);
    
    showStatus(`Club "${clubName}" succesvol toegevoegd!`, "success");
    setClubName("");
  };

  // 2. Iemand admin maken
  const handleMakeAdmin = (e) => {
    e.preventDefault();
    if (!userEmail) return;

    // TODO: Vervang door API call: fetch('/api/admin/promote', { method: 'POST', ... })
    console.log(`Gebruiker ${userEmail} is nu admin`);

    showStatus(`${userEmail} heeft nu admin-rechten.`, "success");
    setUserEmail("");
  };

  // Helper voor feedback
  const showStatus = (text, type) => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: "", type: "" }), 3000);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-extrabold text-gray-900 mb-8">Admin Controlepaneel</h1>

        {/* Feedback melding */}
        {message.text && (
          <div className={`mb-4 p-4 rounded-lg text-white ${message.type === 'success' ? 'bg-green-500' : 'bg-red-500'}`}>
            {message.text}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-8">
          
          {/* Sectie: Clubs Beheren */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <span className="mr-2">🏆</span> Nieuwe Club
            </h2>
            <form onSubmit={handleCreateClub} className="space-y-4">
              <input
                type="text"
                placeholder="Naam van de club..."
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                value={clubName}
                onChange={(e) => setClubName(e.target.value)}
              />
              <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition">
                Club Toevoegen
              </button>
            </form>
          </div>

          {/* Sectie: Gebruikersbeheer */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <span className="mr-2">👤</span> Gebruiker Promoveren
            </h2>
            <form onSubmit={handleMakeAdmin} className="space-y-4">
              <input
                type="email"
                placeholder="E-mailadres van gebruiker..."
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                value={userEmail}
                onChange={(e) => setUserEmail(e.target.value)}
              />
              <button type="submit" className="w-full bg-purple-600 text-white py-2 rounded-lg font-semibold hover:bg-purple-700 transition">
                Maak Admin
              </button>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Admin;