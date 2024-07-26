"use client";

import { useState } from "react";

export default function Home() {
  const [medications, setMedications] = useState([""]);

  const handleInputChange = (
    index: number,
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const values = [...medications];
    values[index] = event.target.value;
    setMedications(values);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-6 bg-gray-50">
      <header className="text-center my-8">
        <h1 className="text-6xl font-bold text-purple-700">Mediract</h1>
        <p className="text-xl text-gray-600 mt-4">
          Search for medications and check for interactions
        </p>
      </header>
      <div className="bg-purple-100 p-8 rounded-lg shadow-lg w-full max-w-2xl">
        <form className="space-y-4">
          <div className="flex flex-col">
            <label
              htmlFor="medication"
              className="text-gray-700 font-medium mb-2"
            >
              Enter a drug, OTC or herbal supplement:
            </label>
            {medications.map((med, index) => (
              <input
                key={index}
                type="text"
                value={med}
                onChange={(event) => handleInputChange(index, event)}
                placeholder="Enter medication"
                className="mb-2 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 text-black"
              />
            ))}
          </div>
        </form>
      </div>
    </main>
  );
}
