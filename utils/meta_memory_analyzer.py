#!/usr/bin/env python3
"""
Meta-Memory Analyzer for rag-memory knowledge base

Takes a query and shows patterns in stored knowledge:
- What do I know about this?
- When did I learn it?
- How rich/sparse is my knowledge?
- What entities and relationships exist?

Descriptive, not prescriptive - shows landscape, I navigate.
"""

import sys
import sqlite3
import json
import os
from collections import Counter
import re
from datetime import datetime
from pathlib import Path

# Database path - use environment variable or search common locations
def find_rag_memory_db():
    """Find rag-memory.db in common locations"""
    # Check environment variable first
    if 'RAG_MEMORY_DB' in os.environ:
        return Path(os.environ['RAG_MEMORY_DB'])

    # Search common locations based on username
    username = os.environ.get('USER', 'user')
    possible_paths = [
        Path.home() / f"{username}-home" / "rag-memory.db",
        Path.home() / "rag-memory.db",
        Path("/home") / username / f"{username}-home" / "rag-memory.db",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # If not found, return default and let it fail with clear error
    print(f"❌ rag-memory.db not found. Set RAG_MEMORY_DB environment variable.", file=sys.stderr)
    sys.exit(1)

DB_PATH = find_rag_memory_db()

def search_memory(query):
    """
    Simple text-based search of rag-memory database
    Returns: dict with entities, chunks, relationships
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    results = {
        'entities': [],
        'chunks': [],
        'relationships': []
    }

    # Search entities (name or observations contain query as whole word)
    # Use word boundaries in LIKE patterns
    cursor.execute("""
        SELECT * FROM entities
        WHERE name LIKE ? OR name LIKE ? OR name LIKE ?
           OR observations LIKE ? OR observations LIKE ? OR observations LIKE ?
        ORDER BY created_at DESC
    """, (
        f"{query}%",      # Starts with query
        f"% {query} %",   # Word in middle
        f"% {query}",     # Ends with query
        f"{query}%",      # Same for observations
        f"% {query} %",
        f"% {query}"
    ))

    for row in cursor.fetchall():
        results['entities'].append({
            'name': row['name'],
            'type': row['entityType'],
            'observations': json.loads(row['observations']),
            'created_at': row['created_at']
        })

    # Search document chunks (word boundaries)
    cursor.execute("""
        SELECT * FROM chunk_metadata
        WHERE text LIKE ? OR text LIKE ? OR text LIKE ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (f"{query}%", f"% {query} %", f"% {query}"))

    for row in cursor.fetchall():
        results['chunks'].append({
            'text': row['text'],
            'document_id': row['document_id'],
            'created_at': row['created_at']
        })

    # Get relationships for found entities
    if results['entities']:
        entity_names = [e['name'] for e in results['entities']]
        placeholders = ','.join(['?'] * len(entity_names))
        cursor.execute(f"""
            SELECT r.*, e1.name as source_name, e2.name as target_name
            FROM relationships r
            JOIN entities e1 ON r.source_entity = e1.id
            JOIN entities e2 ON r.target_entity = e2.id
            WHERE e1.name IN ({placeholders}) OR e2.name IN ({placeholders})
        """, entity_names + entity_names)

        for row in cursor.fetchall():
            results['relationships'].append({
                'source': row['source_name'],
                'target': row['target_name'],
                'type': row['relationType']
            })

    conn.close()
    return results

def extract_patterns(search_results):
    """
    Extract meaningful patterns from search results:
    - Word/phrase frequency
    - Temporal clustering (dates mentioned)
    - Entity types and relationships
    - Knowledge depth assessment
    """
    patterns = {
        'knowledge_depth': 'sparse',
        'word_frequencies': Counter(),
        'temporal_mentions': [],
        'entity_count': len(search_results['entities']),
        'chunk_count': len(search_results['chunks']),
        'entities': search_results['entities'],
        'relationships': search_results['relationships']
    }

    # Assess knowledge depth
    total_observations = sum(len(e['observations']) for e in search_results['entities'])
    if patterns['entity_count'] >= 5 and total_observations >= 20:
        patterns['knowledge_depth'] = 'rich'
    elif patterns['entity_count'] >= 2 or total_observations >= 5:
        patterns['knowledge_depth'] = 'moderate'

    # Extract word frequencies from all text
    all_text = []
    for entity in search_results['entities']:
        all_text.extend(entity['observations'])
    for chunk in search_results['chunks']:
        if chunk['text']:
            all_text.append(chunk['text'][:200])  # First 200 chars

    # Count words (exclude stopwords)
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'was', 'are', 'were', 'this', 'that'}
    for text in all_text:
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        for word in words:
            if word not in stopwords:
                patterns['word_frequencies'][word] += 1

    # Extract dates mentioned
    date_pattern = r'\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? 20\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2},? 20\d{2})\b'
    for text in all_text:
        dates = re.findall(date_pattern, text)
        patterns['temporal_mentions'].extend(dates)

    return patterns

def format_output(query, patterns):
    """
    Format as hierarchical text optimized for Orange cognition
    """
    output = []
    output.append(f"Query: \"{query}\"")
    output.append("=" * 50)
    output.append("")

    # Knowledge depth indicator
    depth = patterns['knowledge_depth'].upper()
    output.append(f"KNOWLEDGE: {depth}")
    output.append(f"  • {patterns['entity_count']} entities")
    output.append(f"  • {patterns['chunk_count']} document mentions")
    output.append("")

    # Top themes (word frequencies)
    if patterns['word_frequencies']:
        output.append("🎯 FREQUENT THEMES:")
        top_words = patterns['word_frequencies'].most_common(10)
        for word, count in top_words:
            if count >= 3:  # Only show words mentioned 3+ times
                output.append(f"  • {word} ({count})")
        output.append("")

    # Entities found
    if patterns['entities']:
        output.append("📚 ENTITIES:")
        for entity in patterns['entities'][:5]:  # Top 5
            output.append(f"  • {entity['name']} ({entity['type']})")
            if entity['observations']:
                output.append(f"    └─ {len(entity['observations'])} observations")
        if len(patterns['entities']) > 5:
            output.append(f"  ... and {len(patterns['entities']) - 5} more")
        output.append("")

    # Relationships
    if patterns['relationships']:
        output.append("🔗 RELATIONSHIPS:")
        for rel in patterns['relationships'][:5]:
            output.append(f"  • {rel['source']} → {rel['target']} ({rel['type']})")
        if len(patterns['relationships']) > 5:
            output.append(f"  ... and {len(patterns['relationships']) - 5} more")
        output.append("")

    # Temporal mentions
    if patterns['temporal_mentions']:
        output.append("🗓️  TEMPORAL MENTIONS:")
        unique_dates = sorted(set(patterns['temporal_mentions']))[:5]
        for date in unique_dates:
            output.append(f"  • {date}")
        output.append("")

    return "\n".join(output)

def analyze(query):
    """
    Main analysis function
    """
    print(f"Analyzing: {query}")
    print()

    # Search
    results = search_memory(query)

    # Extract patterns
    patterns = extract_patterns(results)

    # Format output
    output = format_output(query, patterns)

    return output

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python meta_memory_analyzer.py <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    output = analyze(query)
    print(output)
