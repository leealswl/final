import React from 'react';
import Navbar from './components/Navbar';
import Banner01 from './components/Banner01';
import Banner02 from './components/Banner02';
import Banner03 from './components/Banner03';
import Banner04 from './components/Banner04';

const Homepage = () => {
    return (
        <div>
            <Navbar />
            <Banner01 />
            <Banner02 />
            <Banner03 />
            <Banner04 />
        </div>
    );
};

export default Homepage;
