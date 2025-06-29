"""
Example implementation of the Podcastify FastAPI client.

This module demonstrates how to interact with the Podcastify API
to generate and download podcasts.
"""

import asyncio
import aiohttp
import json
import os
from pathlib import Path
from typing import Dict, Any


def get_default_config() -> Dict[str, Any]:
	"""
	Returns default configuration for podcast generation from URLs.

	Returns:
		Dict[str, Any]: Default configuration dictionary
	"""
	return {
		"generate_podcast": True,
		"google_key": "YOUR_GEMINI_API_KEY",
		"openai_key": "YOUR_OPENAI_API_KEY",
		"urls": ["https://www.phenomenalworld.org/interviews/swap-structure/"],
		"name": "Central Clearing Risks",
		"tagline": "Exploring the complexities of financial systemic risk",
		"creativity": 0.8,
		"conversation_style": ["engaging", "informative"],
		"roles_person1": "main summarizer",
		"roles_person2": "questioner",
		"dialogue_structure": ["Introduction", "Content", "Conclusion"],
		"tts_model": "openai",
		"is_long_form": False,
		"engagement_techniques": ["questions", "examples", "analogies"],
		"user_instructions": "Dont use the world Dwelve",
		"output_language": "English"
	}


def get_text_config() -> Dict[str, Any]:
	"""
	Returns configuration for podcast generation from direct text input.

	Returns:
		Dict[str, Any]: Text-based configuration dictionary
	"""
	return {
		"google_key": "YOUR_GEMINI_API_KEY",
		"openai_key": "YOUR_OPENAI_API_KEY",
		"text": "Artificial Intelligence is revolutionizing how we work, learn, and interact with technology. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions that were previously impossible. From healthcare diagnostics to autonomous vehicles, AI is transforming industries and creating new possibilities for innovation.",
		"name": "AI Insights",
		"tagline": "Understanding the future of technology",
		"creativity": 0.7,
		"conversation_style": ["educational", "accessible"],
		"roles_person1": "AI researcher",
		"roles_person2": "curious journalist",
		"dialogue_structure": ["Introduction", "Key Concepts", "Real-world Applications", "Future Implications"],
		"tts_model": "openai",
		"is_long_form": False,
		"engagement_techniques": ["analogies", "examples"],
		"user_instructions": "Keep explanations accessible to general audience",
		"output_language": "English"
	}


def get_topic_config() -> Dict[str, Any]:
	"""
	Returns configuration for podcast generation from a topic.

	Returns:
		Dict[str, Any]: Topic-based configuration dictionary
	"""
	return {
		"google_key": "YOUR_GEMINI_API_KEY",
		"openai_key": "YOUR_OPENAI_API_KEY",
		"topic": "The impact of quantum computing on cybersecurity",
		"name": "Quantum Security",
		"tagline": "Exploring tomorrow's cybersecurity challenges",
		"creativity": 0.6,
		"conversation_style": ["technical", "forward-thinking"],
		"roles_person1": "quantum computing expert",
		"roles_person2": "cybersecurity analyst",
		"dialogue_structure": ["Current State", "Quantum Threats", "Preparation Strategies", "Timeline"],
		"tts_model": "openai",
		"is_long_form": False,
		"engagement_techniques": ["scenarios", "expert insights"],
		"user_instructions": "Focus on practical implications for businesses",
		"output_language": "English"
	}


async def generate_podcast_from_url() -> None:
	"""
	Generates a podcast from URLs using the Podcastify API.
	"""
	await generate_podcast_with_config(get_default_config(), "URL-based podcast")


async def generate_podcast_from_text() -> None:
	"""
	Generates a podcast from direct text input using the Podcastify API.
	"""
	await generate_podcast_with_config(get_text_config(), "Text-based podcast")


async def generate_podcast_from_topic() -> None:
	"""
	Generates a podcast from a topic using the Podcastify API.
	"""
	await generate_podcast_with_config(get_topic_config(), "Topic-based podcast")


async def generate_podcast_with_config(config: Dict[str, Any], description: str) -> None:
	"""
	Generates a podcast using the provided configuration.
	
	Args:
		config (Dict[str, Any]): Configuration for podcast generation
		description (str): Description of the podcast type for logging
	"""
	async with aiohttp.ClientSession() as session:
		try:
			print(f"Starting {description} generation...")
			async with session.post(
				"http://localhost:8080/generate",
				json=config
			) as response:
				if response.status != 200:
					print(f"Error: Server returned status {response.status}")
					return
				
				result = await response.json()
				if "error" in result:
					print(f"Error: {result['error']}")
					return

				await download_podcast(session, result)

		except aiohttp.ClientError as e:
			print(f"Network error: {str(e)}")
		except Exception as e:
			print(f"Unexpected error: {str(e)}")


async def download_podcast(session: aiohttp.ClientSession, result: Dict[str, str]) -> None:
	"""
	Downloads the generated podcast file.

	Args:
		session (aiohttp.ClientSession): Active client session
		result (Dict[str, str]): API response containing audioUrl
	"""
	audio_url = f"http://localhost:8080{result['audioUrl']}"
	print(f"Podcast generated! Downloading from: {audio_url}")

	async with session.get(audio_url) as audio_response:
		if audio_response.status == 200:
			filename = os.path.join(
				str(Path.home() / "Downloads"), 
				result['audioUrl'].split('/')[-1]
			)
			with open(filename, 'wb') as f:
				f.write(await audio_response.read())
			print(f"Downloaded to: {filename}")
		else:
			print(f"Failed to download audio. Status: {audio_response.status}")


async def main():
	"""
	Main function to demonstrate different input types for podcast generation.
	"""
	print("Podcastify API Examples")
	print("=" * 50)
	print("Choose an input type:")
	print("1. Generate from URLs")
	print("2. Generate from direct text")
	print("3. Generate from topic")
	print("4. Run all examples")
	
	choice = input("\nEnter your choice (1-4): ").strip()
	
	if choice == "1":
		await generate_podcast_from_url()
	elif choice == "2":
		await generate_podcast_from_text()
	elif choice == "3":
		await generate_podcast_from_topic()
	elif choice == "4":
		print("\nRunning all examples...")
		await generate_podcast_from_url()
		print("\n" + "="*50 + "\n")
		await generate_podcast_from_text()
		print("\n" + "="*50 + "\n")
		await generate_podcast_from_topic()
	else:
		print("Invalid choice. Please run the script again and choose 1-4.")


if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		print("\nProcess interrupted by user")
	except Exception as e:
		print(f"Error: {str(e)}")