from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# remove blank lines
install_requires = [r for r in install_requires if r and not r.startswith("#")]

setup(
	name="qatar_gratuity",
	version="1.0.0",
	description="Qatar Labour Law Gratuity Calculation for ERPNext 15",
	author="Your Company",
	author_email="admin@yourcompany.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
)
