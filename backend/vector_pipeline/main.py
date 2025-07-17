#!/usr/bin/env python3
"""
Vector Pipeline Main Module

This module provides the main interface for the vector pipeline system.
It orchestrates all components and provides a clean API for external usage.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.vector_processor import VectorProcessor
from core.text_chunker import TextChunker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VectorPipeline:
    """
    Main Vector Pipeline class that orchestrates all components.
    
    This class provides a unified interface for all vector pipeline operations
    including text processing and embedding generation.
    """
    
    def __init__(self):
        """Initialize the Vector Pipeline."""
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize all pipeline components."""
        try:
            # Core components
            self.vector_processor = VectorProcessor()
            self.text_chunker = TextChunker()
            
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise
    
    def process_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a single text through the complete pipeline.
        
        Args:
            text: Input text to process
            metadata: Optional metadata for the text
            
        Returns:
            Dictionary containing processed results
        """
        try:
            # Step 1: Text chunking
            document_id = metadata.get('document_id', 'default') if metadata else 'default'
            chunks = self.text_chunker.split_text_into_chunks(text, document_id)
            
            # Step 2: Generate embeddings
            chunk_texts = [chunk.chunk_text for chunk in chunks]
            embeddings = self.vector_processor.generate_embeddings(chunk_texts)
            
            # Step 3: Prepare data for storage
            processed_data = []
            for i, chunk in enumerate(chunks):
                processed_data.append({
                    'chunk_id': chunk.chunk_id,
                    'chunk_text': chunk.chunk_text,
                    'embedding': embeddings[i].tolist(),
                    'metadata': metadata or {}
                })
            
            return {
                'status': 'success',
                'chunks': len(chunks),
                'embeddings': len(embeddings),
                'processed_data': processed_data
            }
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def batch_process(self, texts: List[str], metadata_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Process multiple texts in batch.
        
        Args:
            texts: List of texts to process
            metadata_list: Optional list of metadata for each text
            
        Returns:
            Dictionary containing batch processing results
        """
        try:
            results = []
            for i, text in enumerate(texts):
                metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
                result = self.process_text(text, metadata)
                results.append(result)
            
            return {
                'status': 'success',
                'total_processed': len(texts),
                'successful': len([r for r in results if r['status'] == 'success']),
                'failed': len([r for r in results if r['status'] == 'error']),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def search_similar(self, query: str, texts: List[str], limit: int = 10) -> Dict[str, Any]:
        """
        Search for similar content using vector similarity.
        
        Args:
            query: Search query
            texts: List of texts to search in
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing search results
        """
        try:
            # Generate embedding for query
            query_embedding = self.vector_processor.generate_single_embedding(query)
            
            # Generate embeddings for all texts
            text_embeddings = self.vector_processor.generate_embeddings(texts)
            
            # Calculate similarities
            similarities = self.vector_processor.calculate_similarities(query, texts)
            
            # Sort by similarity and get top results
            text_similarity_pairs = list(zip(texts, similarities))
            text_similarity_pairs.sort(key=lambda x: x[1], reverse=True)
            
            top_results = text_similarity_pairs[:limit]
            
            results = []
            for text, similarity in top_results:
                results.append({
                    'text': text,
                    'similarity': similarity
                })
            
            return {
                'status': 'success',
                'query': query,
                'results_count': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.
        
        Returns:
            Dictionary containing model information
        """
        try:
            return self.vector_processor.get_model_info()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get the current status of all pipeline components.
        
        Returns:
            Dictionary containing component statuses
        """
        try:
            model_info = self.get_model_info()
            return {
                'vector_processor': 'available',
                'text_chunker': 'available',
                'model_info': model_info
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


# Convenience functions for easy usage
def create_pipeline() -> VectorPipeline:
    """Create and return a new VectorPipeline instance."""
    return VectorPipeline()


def process_single_text(text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Process a single text using a default pipeline instance."""
    pipeline = VectorPipeline()
    return pipeline.process_text(text, metadata)


def search_similar_content(query: str, texts: List[str], limit: int = 10) -> Dict[str, Any]:
    """Search for similar content using a default pipeline instance."""
    pipeline = VectorPipeline()
    return pipeline.search_similar(query, texts, limit)


if __name__ == "__main__":
    # Example usage
    pipeline = VectorPipeline()
    
    # Process a sample text
    sample_text = "This is a sample text for testing the vector pipeline."
    result = pipeline.process_text(sample_text, {'source': 'test'})
    print(f"Processing result: {result}")
    
    # Search for similar content
    sample_texts = [
        "This is a sample text for testing.",
        "Another example text for comparison.",
        "A completely different topic about technology."
    ]
    search_result = pipeline.search_similar("sample text", sample_texts)
    print(f"Search result: {search_result}")
    
    # Get model info
    model_info = pipeline.get_model_info()
    print(f"Model info: {model_info}") 