'use client'

import { useState } from 'react'

import type { Question } from '@/lib/quiz'

// Two questions at the end of a chapter. Pick an answer and see why it is right or wrong.

function One({ question, index }: { question: Question; index: number }) {
  const [picked, setPicked] = useState<number | null>(null)
  const right = picked === question.answer
  return (
    <fieldset className="flex flex-col gap-3">
      <legend className="mb-3 text-[16px] font-semibold text-ink">
        <span className="mr-2 font-mono text-[13px] text-blue-text">Q{index + 1}</span>
        {question.q}
      </legend>
      <div className="flex flex-col gap-2">
        {question.options.map((option, choice) => {
          const chosen = picked === choice
          const look =
            picked === null
              ? 'border-rule-strong hover:border-blue'
              : choice === question.answer
                ? 'border-pass bg-pass-wash text-pass'
                : chosen
                  ? 'border-fail bg-fail-wash text-fail'
                  : 'border-rule opacity-70'
          return (
            <button
              key={option}
              type="button"
              disabled={picked !== null}
              onClick={() => setPicked(choice)}
              className={`flex min-h-11 items-center gap-3 rounded-md border bg-surface px-3.5 py-2 text-left text-[15px] ${look}`}
            >
              <span aria-hidden="true" className="font-mono text-[12px] text-muted">
                {String.fromCharCode(65 + choice)}
              </span>
              {option}
            </button>
          )
        })}
      </div>
      {picked !== null ? (
        <p role="status" className="text-[15px] leading-relaxed text-ink-2">
          <strong className={right ? 'text-pass' : 'text-fail'}>
            {right ? 'Right.' : 'Not quite.'}
          </strong>{' '}
          {question.why}
        </p>
      ) : null}
    </fieldset>
  )
}

export function Quiz({ questions }: { questions: readonly Question[] }) {
  return (
    <section aria-labelledby="check-yourself" className="card flex flex-col gap-7 p-5 sm:p-7">
      <div>
        <span className="eyebrow">Check yourself</span>
        <h2 id="check-yourself" className="mt-1 text-[22px] font-semibold tracking-[-0.01em]">
          Two questions before you move on
        </h2>
      </div>
      {questions.map((question, index) => (
        <One key={question.q} question={question} index={index} />
      ))}
    </section>
  )
}
