import { isValidElement, type ReactNode } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { CopyButton } from './CopyButton'

// A chapter body rendered like good documentation: code blocks with a labelled header and a copy
// button, tables that scroll on their own on a phone, and headings you can link to.

const LABELS: Record<string, string> = {
  bash: 'shell',
  text: 'output',
  python: 'python',
  dockerfile: 'Dockerfile',
  yaml: 'compose.yaml',
  sql: 'sql',
  json: 'json',
}

function textOf(node: ReactNode): string {
  if (typeof node === 'string' || typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(textOf).join('')
  if (isValidElement<{ children?: ReactNode }>(node)) return textOf(node.props.children)
  return ''
}

function languageOf(node: ReactNode): string {
  const child = Array.isArray(node) ? node[0] : node
  if (!isValidElement<{ className?: string }>(child)) return ''
  return /language-(\w+)/.exec(child.props.className ?? '')?.[1] ?? ''
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
}

/** The chapter's second-level headings, for the "On this page" outline. */
export function headingsOf(body: string): { id: string; text: string }[] {
  const outside = body.replace(/```[\s\S]*?```/g, '')
  return [...outside.matchAll(/^## (.+)$/gm)].map((match) => {
    const text = (match[1] ?? '').replace(/`/g, '')
    return { id: slugify(text), text }
  })
}

const components: Components = {
  pre({ children }) {
    const language = languageOf(children)
    const output = language === 'text'
    return (
      <div className={`code-block${output ? ' is-output' : ''}`}>
        <div className="code-head">
          <span>{LABELS[language] ?? (language || 'code')}</span>
          <CopyButton text={textOf(children).replace(/\n$/, '')} />
        </div>
        <pre>{children}</pre>
      </div>
    )
  },
  h2({ children }) {
    const id = slugify(textOf(children))
    return (
      <h2 id={id}>
        {children}
        <a href={`#${id}`} className="anchor" aria-label={`Link to ${textOf(children)}`}>
          #
        </a>
      </h2>
    )
  },
  table({ children }) {
    return (
      <div className="table-wrap">
        <table>{children}</table>
      </div>
    )
  },
}

export function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {children}
    </ReactMarkdown>
  )
}
