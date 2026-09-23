set -e

if [ -d "frontend" ] && command -v npm >/dev/null 2>&1; then
  cd frontend
  npm install
  npm run build
  cd ..
  mkdir -p backend/static
  cp -r frontend/dist/* backend/static/
fi

pip install --upgrade pip
pip install -r backend/requirements.txt
