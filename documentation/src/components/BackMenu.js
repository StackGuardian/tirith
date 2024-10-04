import React from 'react';
import { Link } from 'docusaurus/router';

const BackMenu = () => {
  return (
    <Link to="/" className="back-to-main-menu">
      Back
    </Link>
  );
};

export default BackMenu;