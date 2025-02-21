from setuptools import setup, find_packages

# Чтение версии из __init__.py
with open("ai_assistant/__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"')
            break

setup(
    name="ai_assistant",
    version=version,
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.31.0",
        "python-dotenv>=1.0.1",
        "requests>=2.31.0",
        "duckduckgo-search>=7.4.4",
        "openai>=1.12.0",
        "jinja2>=3.1.3",
        "typing-extensions>=4.9.0",
        "python-logging-loki>=0.3.1",
        "anthropic>=0.18.1",
        "tiktoken>=0.5.2",
        "cryptography>=42.0.4"
    ],
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "ai_assistant": ["prompts/*"],
    },
) 