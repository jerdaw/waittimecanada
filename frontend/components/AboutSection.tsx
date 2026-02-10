"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Github, Linkedin, Mail } from "lucide-react";

export function AboutSection() {
  const [expanded, setExpanded] = useState(false);

  return (
    <section className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-900 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between text-left hover:opacity-80 transition-opacity"
          aria-expanded={expanded}
          aria-label={
            expanded ? "Collapse about section" : "Expand about section"
          }
        >
          <div>
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wide">
              About This Project
            </span>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
              Why I Built WaitTime Canada
            </h2>
          </div>
          {expanded ? (
            <ChevronUp className="w-6 h-6 text-slate-400 flex-shrink-0" />
          ) : (
            <ChevronDown className="w-6 h-6 text-slate-400 flex-shrink-0" />
          )}
        </button>

        {expanded && (
          <div className="mt-6 space-y-4 text-slate-600 dark:text-slate-300 animate-in fade-in slide-in-from-top-4 duration-300">
            <p>
              As a pre-medical student, I noticed something troubling: Canadian
              provinces report emergency room wait times using{" "}
              <strong>completely different methodologies</strong>. Ontario
              measures from triage to physician (90th percentile). Quebec
              measures from registration to physician (rolling average). These
              numbers can&apos;t be directly compared—but most apps present them
              side-by-side anyway.
            </p>

            <p>
              <strong>WaitTime Canada is different.</strong> Instead of
              pretending the data is comparable, we audit it. We tag every
              measurement with its methodology and warn users when direct
              comparison is statistically invalid. This is what I call a
              &quot;Health Systems Observatory&quot;—a tool that exposes the
              black box of healthcare reporting.
            </p>

            <p>
              This project demonstrates my approach to medicine: rigorous
              methodology, transparent limitations, and a commitment to helping
              patients make informed decisions—even when that means telling them
              what we <em>don&apos;t</em> know.
            </p>

            <div className="flex items-center gap-6 pt-4 border-t border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <div
                  className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg"
                  aria-label="Author avatar"
                >
                  JD
                </div>
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    Jeremy Dawson
                  </p>
                  <p className="text-sm text-slate-500">Pre-Medical Student</p>
                </div>
              </div>
              <div className="flex gap-3">
                <a
                  href="https://github.com/jerdaw/waittimecanada"
                  className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                  aria-label="View on GitHub"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Github className="w-5 h-5" />
                </a>
                <a
                  href="https://linkedin.com/in/jeremyjdawson"
                  className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                  aria-label="LinkedIn profile"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Linkedin className="w-5 h-5" />
                </a>
                <a
                  href="mailto:jeremyjdawson@gmail.com"
                  className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                  aria-label="Email contact"
                >
                  <Mail className="w-5 h-5" />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
