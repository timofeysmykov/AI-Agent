from setuptools import setup, find_packages

setup(
    name="ai_assistant",
    version="0.1.0",
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
    ],
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "ai_assistant": ["prompts/*"],
    },
) 