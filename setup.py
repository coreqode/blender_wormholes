from setuptools import setup, find_packages

with open('requirements.txt') as f:
	requirements = f.readlines()

long_description = 'helper library'

setup(
		name ='blender_wormholes',
		version ='0.0.1',
		author ='Chandradeep Pokhariya',
		author_email ='cdpokhariya@gmail.com',
		url ='https://github.com/coreqode/blender_wormholes',
		description ='helper library',
		long_description = long_description,
		long_description_content_type ="text/markdown",
		license ='MIT',
		#  packages = find_packages(),
		entry_points ={
			'console_scripts': [
				'wh = blender_wormholes.__main__:main'
			]
		},
		classifiers =(
			"Programming Language :: Python :: 3",
			"License :: OSI Approved :: MIT License",
			"Operating System :: OS Independent",
		),
        packages = [
            'blender_wormholes',
        ],
		install_requires = requirements,
		zip_safe = False
)

