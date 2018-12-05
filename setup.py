from setuptools import setup


setup(name='brainimageshare',
      version='0.1',
      description='Create jpeg with contact overlay from a nifti brain image',
      classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
      ],
      keywords='share brain image nifti mprage',
      url='http://github.com/LabNeuroCogDevel/BrainImageShare',
      author='Will Foran',
      author_email='WillForan+py@gmail.com',
      license='GPLv3',
      packages=['brainimageshare'],
      install_requires=[
          'Pillow',
          'nibabel',
      ],
      entry_points={
          'gui': ['brainimageshare = brainimageshare:brainimageshare'],
      },
      scripts=['bin/brainimageshare'],
      data_files=[('templates', ['templates/overlay.png'])],
      include_package_data=True,
      zip_safe=False)
