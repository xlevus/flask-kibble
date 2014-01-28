import sys, os

appstats_MAX_STACK = 20

package_dir = "packages"
package_dir_path = os.path.join(os.path.dirname(__file__), package_dir)

for filename in sorted(os.listdir(package_dir_path)):
    pth_file = os.path.join(package_dir_path, filename)
    if filename.endswith('.whl'):
        sys.path.insert(0, pth_file)
sys.path.insert(0, package_dir_path)



