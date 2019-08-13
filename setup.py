# flake8: noqa
# encoding: utf-8
#
# A modifier: 
#        toute occurrence de "altictoh"/package_name 
#        packages=find_packages(exclude.....
#        install_requires
#        entry_points

from setuptools import setup, find_packages, Extension, find_namespace_packages
import sys, os
import numpy
import vcversioner

package_name='altis'

from setuptools.command.install import install

package_version=vcversioner.find_version(
        version_module_paths=['%s/_version.py' % package_name]).version
package_sha=vcversioner.find_version(
        version_module_paths=['%s/_version.py' % package_name]).sha

version = package_version+'_'+package_sha


class CustomInstall(install):
    def run(self):
        print("hello pre_install_message")
        install.run(self)
        print("post_install_message")

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(name=package_name,
      version=version,
      description="Altimetry Times Series Software (AlTiS Software)",
      long_description=long_description,
      classifiers=[
                "Topic :: Scientific/Engineering :: Physics",
                "Intended Audience :: Science/Research",
                "Development Status :: 4 - Beta",
                "Programming Language :: Python :: 3",
                "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                "Operating System :: OS Independent",
                ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='radar altimetry, time series, hydrology, normalized pass',
      author='CTOH',
      author_email='frappart@legos.obs-mip.fr,  blarel@legos.obs-mip.fr, \
                    ctoh_products@legos.obs-mip.fr',
      url='http://ctoh.legos.obs-mip.fr/land_surfaces/softwares/...',
      license='GPLv3',
      packages=find_namespace_packages('.',exclude=['tests']),
      package_data={package_name:['LICENSE','etc/*.yml','doc/*','examples/*']},
      include_package_data=False,
      zip_safe=False,
      setup_requires=['vcversioner'],
      vcversioner={'version_module_paths': ['%s/_version.py' % package_name]},
      #cmdclass={'install': CustomInstall},
#      install_requires=[
#          "numpy>=1.8",
#          "configobj>5",
          # -*- Extra requirements: -*-
#      ],
      python_requires='>=3',
      entry_points={
          'console_scripts': [
               'altis_gui = %s.altis_gui:main' % package_name,
        ]
      },)



